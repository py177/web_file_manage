cat <<'EOF' > filesu_test.py
import os
import sys
import urllib.parse
import re
import logging
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename, safe_join

# 引入 neo4j 和 pandas
from neo4j import GraphDatabase
import pandas as pd

# 配置 logging 输出到标准输出
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    stream=sys.stdout)

# 确保 Flask 运行环境为 UTF-8
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# 允许中文文件名的处理函数：仅去除首尾空格和非法字符，保留中间空格
def secure_filename_cn(filename):
    filename = filename.strip()
    filename = re.sub(r'[\/:*?"<>|]', '', filename)
    return filename

# 自定义过滤器：格式化时间戳
@app.template_filter('datetimeformat')
def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

# 文件存放目录及默认分页设置
#FILE_DIRECTORY = "/Users/qianqian.li3/Desktop/test/data/"
FILE_DIRECTORY = "/data/"
DEFAULT_PER_PAGE = 10

# 从知识图谱中查询所有 Document 节点的文件名（不含扩展名），返回一个集合
def get_kg_file_names():
    db = 'graphrag'
    neo4j_url = 'bolt://10.132.252.15:7687'
    driver = GraphDatabase.driver(neo4j_url, auth=(("API_SERVER", "Pass1234")))
    session = driver.session(database=db)
    query = "MATCH (d:Document) RETURN d.fileName AS fileName"
    results = session.run(query)
    # 假设知识图谱中的文件名均不含扩展名
    kg_files = {record["fileName"] for record in results if record["fileName"]}
    session.close()
    driver.close()
    return kg_files

# 获取当前路径下的所有文件和文件夹
def get_files_and_folders(current_path):
    current_path = request.form.get('current_path', current_path)
    print(f"Current Path3: {current_path}")
    try:
        with os.scandir(current_path) as entries:
            return [
                {'name': entry.name,
                 'size': entry.stat().st_size if entry.is_file() else '-',
                 'mtime': entry.stat().st_mtime,
                 'type': 'file' if entry.is_file() else 'folder'}
                for entry in entries
            ]
    except FileNotFoundError:
        return []

@app.route('/')
@app.route('/<path:current_path>')
def index(current_path=FILE_DIRECTORY):
    # 调试打印路径和文件
    print(f"Current Path1: {current_path}")
    files_and_folders = get_files_and_folders(current_path)
    #print(f"Files and Folders: {files_and_folders}")
    
    # 获取请求参数
    try:
        page = int(request.args.get('page', 1))  # 获取当前页码
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', DEFAULT_PER_PAGE))  # 获取每页显示的数量
    except ValueError:
        per_page = DEFAULT_PER_PAGE

    sort_by = request.args.get('sort_by', 'name')
    reverse = request.args.get('reverse', 'false').lower() == 'true'
    search_query = request.args.get('search', '').strip()
    filter_kg = request.args.get('filter_kg')  # "1" 表示仅显示在图谱中的，"0" 表示仅显示不在图谱中的
    bulk = request.args.get('bulk') == '1'

    # 获取当前路径，优先使用查询参数中的 `current_path`
    # current_path = request.form.get('current_path', current_path)

    # 确保路径是绝对路径
    if not current_path.startswith('/'):
        current_path = '/' + current_path

    files_and_folders = get_files_and_folders(current_path)
    #print(files_and_folders)
    print(f"Current Path2: {current_path}")
    
    # 修正搜索逻辑：仅在当前目录下搜索
    if search_query:
        files_and_folders = [
            f for f in files_and_folders
            if search_query.lower() in f['name'].lower()  # 搜索文件名
        ]
        print(f"Current Path4: {current_path}")

    # 排序逻辑
    if sort_by == 'size':
        files_and_folders.sort(key=lambda x: (x['type'] == 'file', x['size'] if x['type'] == 'file' else 0), reverse=reverse)
    elif sort_by == 'mtime':
        files_and_folders.sort(key=lambda x: x['mtime'], reverse=reverse)
    else:
        files_and_folders.sort(key=lambda x: (x['type'] == 'file', x['name']), reverse=reverse)

    # 查询知识图谱中的所有文件基本名（不含扩展名）
    kg_file_names = get_kg_file_names()
    # 对文件列表中每个文件（仅针对 file 类型）添加 base_name 和 in_kg 字段
    for file in files_and_folders:
        if file["type"] == "file":
            base_name = os.path.splitext(file["name"])[0]
            file["base_name"] = base_name
            file["in_kg"] = (base_name in kg_file_names)

    # 根据筛选参数过滤文件列表（仅针对 file 类型）
    if filter_kg is not None:
        files_and_folders = [f for f in files_and_folders if f["type"] != "file" or (f["type"] == "file" and ((filter_kg=="1" and f["in_kg"]) or (filter_kg=="0" and not f["in_kg"])))]
    
    # 计算经过滤后的pdf文件总数（用于统计显示）
    total_pdf_count = sum(1 for f in files_and_folders if f["type"] == "file" and f["name"].lower().endswith('.pdf'))

    # 分页处理
    total_pages = max(1, (len(files_and_folders) + per_page - 1) // per_page)
    paged_files = files_and_folders[(page - 1) * per_page: page * per_page]

    return render_template("index.html",
                           files_and_folders=paged_files,
                           page=page,
                           total_pages=total_pages,
                           per_page=per_page,
                           sort_by=sort_by,
                           reverse=reverse,
                           search=search_query,
                           filter_kg=filter_kg,
                           bulk=bulk,
                           current_path=current_path,
                           total_pdf_count=total_pdf_count)


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

@app.route('/check_uploaded_pdfs', methods=['GET'])
def check_uploaded_pdfs():
    current_path = request.args.get('current_path', FILE_DIRECTORY)
    uploaded_pdf_files = []
    for root, dirs, files in os.walk(current_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                uploaded_pdf_files.append(os.path.join(root, file))
    db = 'graphrag'
    neo4j_url = 'bolt://10.132.252.15:7687'
    driver = GraphDatabase.driver(neo4j_url, auth=(("API_SERVER", "Pass1234")))
    session = driver.session(database=db)
    query = 'MATCH (n:Document) WHERE toLower(trim(n.fileName)) = toLower(trim($pdf_name)) RETURN n'
    exists_list = []
    not_exists_list = []
    for pdf_path in uploaded_pdf_files:
        pdf_name = os.path.splitext(os.path.basename(pdf_path).strip())[0]
        if not pdf_name:
            continue
        result = session.run(query, pdf_name=pdf_name)
        df_test = pd.DataFrame([dict(record) for record in result]).drop_duplicates()
        if not df_test.empty:
            exists_list.append(pdf_name)
        else:
            not_exists_list.append(pdf_name)
    session.close()
    driver.close()
    logging.info("Detected files in the Knowledge Graph: %s", exists_list)
    # 传入分页相关默认值，避免模板中 total_pages 未定义
    return render_template("index.html",
                           exists_list=exists_list,
                           not_exists_list=not_exists_list,
                           current_path=current_path,
                           page=1,
                           total_pages=1,
                           per_page=DEFAULT_PER_PAGE,
                           sort_by="name",
                           reverse=False,
                           search="",
                           filter_kg=None,
                           bulk=False,
                           total_pdf_count=0)

@app.route('/show_kg_files', methods=['GET'])
def show_kg_files():
    db = 'graphrag'
    neo4j_url = 'bolt://10.132.252.15:7687'
    driver = GraphDatabase.driver(neo4j_url, auth=(("API_SERVER", "Pass1234")))
    session = driver.session(database=db)
    query = "MATCH (n:Document) RETURN n.fileName AS fileName"
    results = session.run(query)
    kg_files = [record["fileName"] for record in results if record["fileName"]]
    session.close()
    driver.close()
    logging.info("Knowledge Graph files: %s", kg_files)
    return render_template("index.html", kg_files=kg_files)

@app.route('/update_kg', methods=['POST'])
def update_kg():
    action = request.form.get("action")  # "add" 或 "remove"
    file_name = request.form.get("file_name")  # 文件基本名（不含扩展名）
    current_path = request.form.get("current_path", FILE_DIRECTORY)
    db = 'graphrag'
    neo4j_url = 'bolt://10.132.252.15:7687'
    driver = GraphDatabase.driver(neo4j_url, auth=(("API_SERVER", "Pass1234")))
    session = driver.session(database=db)
    if action == "add":
         query = "MERGE (d:Document {fileName: $file_name}) RETURN d"
         session.run(query, file_name=file_name)
    elif action == "remove":
         query = "MATCH (d:Document {fileName: $file_name}) DETACH DELETE d"
         session.run(query, file_name=file_name)
    session.close()
    driver.close()
    return redirect(url_for('index', current_path=current_path))

@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = secure_filename_cn(request.form.get('folder_name'))
    current_path = request.form.get('current_path', FILE_DIRECTORY)

    if not folder_name:
        return "文件夹名称不能为空", 400
    folder_path = os.path.join(current_path, folder_name)
    if os.path.exists(folder_path):
        return "文件夹已存在", 400
    os.makedirs(folder_path)
    
    # 重定向到当前路径
    return redirect(url_for('index', current_path=current_path))

@app.route('/files/<path:filename>')
def serve_file(filename):
    decoded_filename = urllib.parse.unquote(filename)
    current_path = request.args.get('current_path', FILE_DIRECTORY)
    full_path = os.path.join(current_path, decoded_filename)
    if os.path.isdir(full_path):
        import tempfile, shutil
        from flask import after_this_request
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp.close()
        archive_name = temp.name[:-4]
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

@app.route('/bulk_action', methods=['POST'])
def bulk_action():
    action = request.form.get('action')
    current_path = request.form.get('current_path', FILE_DIRECTORY)
    selected_files = request.form.getlist('selected_files')
    if not selected_files:
        return "未选择文件", 400
    if action == 'delete':
        for file in selected_files:
            full_path = os.path.join(current_path, file)
            if os.path.isfile(full_path):
                os.remove(full_path)
        return redirect(url_for('index', current_path=current_path))
    elif action in ('add', 'remove'):
        db = 'graphrag'
        neo4j_url = 'bolt://10.132.252.15:7687'
        driver = GraphDatabase.driver(neo4j_url, auth=(("API_SERVER", "Pass1234")))
        session = driver.session(database=db)
        for file in selected_files:
            base_name = os.path.splitext(file)[0]
            if action == 'add':
                query = "MERGE (d:Document {fileName: $file_name}) RETURN d"
                session.run(query, file_name=base_name)
            else:
                query = "MATCH (d:Document {fileName: $file_name}) DETACH DELETE d"
                session.run(query, file_name=base_name)
        session.close()
        driver.close()
        return redirect(url_for('index', current_path=current_path))
    else:
        return "无效的操作", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

EOF
