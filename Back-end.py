# 创建 Python 文件
import os
import sys
import urllib.parse
import re
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename, safe_join

# 确保 Flask 运行环境是 UTF-8
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# 允许中文文件名
def secure_filename_cn(filename):
    filename = filename.strip().replace(' ', '_')
    filename = re.sub(r'[\/:*?"<>|]', '', filename)
    return filename

# Jinja2 过滤器，格式化时间
@app.template_filter('datetimeformat')
def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

# 文件存放目录
FILE_DIRECTORY = "/data/dify_tp_files"
DEFAULT_PER_PAGE = 10  # 默认每页显示数量

# 获取当前路径下的所有文件和文件夹
def get_files_and_folders(current_path):
    try:
        with os.scandir(current_path) as entries:
            return [
                {'name': entry.name, 'size': entry.stat().st_size if entry.is_file() else '-', 'mtime': entry.stat().st_mtime, 'type': 'file' if entry.is_file() else 'folder'}
                for entry in entries
            ]
    except FileNotFoundError:
        return []

@app.route('/')
@app.route('/<path:current_path>')
def index(current_path=FILE_DIRECTORY):
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', DEFAULT_PER_PAGE))
    except ValueError:
        per_page = DEFAULT_PER_PAGE
    sort_by = request.args.get('sort_by', 'name')
    reverse = request.args.get('reverse', 'false').lower() == 'true'
    search_query = request.args.get('search', '').strip()
    # Normalize current_path to always start with '/'
    if not current_path.startswith('/'):
        current_path = '/' + current_path

    files_and_folders = get_files_and_folders(current_path)

    if search_query:
        files_and_folders = [f for f in files_and_folders if search_query.lower() in f['name'].lower()]

    # 排序逻辑
    if sort_by == 'size':
        files_and_folders.sort(key=lambda x: (x['type'] == 'file', x['size'] if x['type'] == 'file' else 0), reverse=reverse)
    elif sort_by == 'mtime':
        files_and_folders.sort(key=lambda x: x['mtime'], reverse=reverse)
    else:
        files_and_folders.sort(key=lambda x: (x['type'] == 'file', x['name']), reverse=reverse)

    total_pages = max(1, (len(files_and_folders) + per_page - 1) // per_page)
    files_and_folders = files_and_folders[(page - 1) * per_page: page * per_page]

    return render_template("index.html", files_and_folders=files_and_folders, page=page, total_pages=total_pages, per_page=per_page, sort_by=sort_by, reverse=reverse, search=search_query, current_path=current_path)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or request.files['file'].filename == '':
        return "未选择文件", 400

    file = request.files['file']
    filename = secure_filename_cn(urllib.parse.unquote(file.filename))
    current_path = request.form.get('current_path', FILE_DIRECTORY)
    file.save(os.path.join(current_path, filename))
    return redirect(url_for('index', current_path=current_path))

@app.route('/upload_folder', methods=['POST'])
def upload_folder():
    current_path = request.form.get('current_path', FILE_DIRECTORY)
    files = request.files.getlist('folder')
    if not files:
        return "未选择文件夹", 400
    for file in files:
        if file.filename == '':
            continue
        parts = file.filename.split('/')
        secure_parts = [secure_filename_cn(part) for part in parts if part]
        final_path = os.path.join(current_path, *secure_parts)
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        file.save(final_path)
    return redirect(url_for('index', current_path=current_path))

@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = secure_filename_cn(request.form.get('folder_name'))
    if not folder_name:
        return "文件夹名称不能为空", 400

    folder_path = os.path.join(FILE_DIRECTORY, folder_name)
    if os.path.exists(folder_path):
        return "文件夹已存在", 400

    os.makedirs(folder_path)
    return redirect(url_for('index'))

@app.route('/files/<path:filename>')
def serve_file(filename):
    decoded_filename = urllib.parse.unquote(filename)
    current_path = request.args.get('current_path', FILE_DIRECTORY)
    full_path = os.path.join(current_path, decoded_filename)
    if os.path.isdir(full_path):
        import tempfile
        import shutil
        from flask import after_this_request
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp.close()
        archive_name = temp.name[:-4]  # 去掉 .zip 后缀以构造归档文件名
        shutil.make_archive(archive_name, 'zip', full_path)
        zip_path = archive_name + '.zip'
        @after_this_request
        def cleanup(response):
            os.remove(zip_path)
            return response
        return send_from_directory(os.path.dirname(zip_path), os.path.basename(zip_path), as_attachment=True)
    else:
        return send_from_directory(current_path, decoded_filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete_file_or_folder(filename):
    confirmed = request.args.get('confirmed', 'false').lower() == 'true'
    current_path = request.args.get('current_path', FILE_DIRECTORY)
    decoded_filename = urllib.parse.unquote(filename)
    full_path = os.path.join(current_path, decoded_filename)
    if os.path.isdir(full_path):
        if os.listdir(full_path):
            if confirmed:
                import shutil
                shutil.rmtree(full_path)
            else:
                return "OSError: [Errno 39] Directory not empty: '{}'".format(full_path)
        else:
            os.rmdir(full_path)
    else:
        os.remove(full_path)
    return redirect(url_for('index', current_path=current_path))

@app.route('/rename/<old_name>', methods=['POST'])
def rename_file_or_folder(old_name):
    old_name = urllib.parse.unquote(old_name)
    new_name = secure_filename_cn(request.form.get('new_name'))

    if not new_name:
        return redirect(url_for('index'))

    old_path = os.path.join(FILE_DIRECTORY, old_name)
    new_path = os.path.join(FILE_DIRECTORY, new_name)

    if os.path.exists(new_path):
        return "目标名称已存在", 400

    os.rename(old_path, new_path)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
