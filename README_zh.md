# 文件管理系统

[English Version](README.md) | [中文版本](README_zh.md)

该项目是一个基于 Python 和 Flask 构建的文件管理系统，提供了一个 Web 界面用于上传、下载（文件夹下载时会先压缩为 ZIP 文件）、重命名和删除文件及文件夹。系统还支持排序、分页和搜索功能。

## 操作步骤

1. **克隆仓库**
   - 打开终端并执行：
     ```bash
     git clone https://github.com/yourusername/your-repo-name.git
     ```
   - （请将 URL 替换为你实际的仓库地址）

2. **进入项目目录**
   - 切换到仓库目录：
     ```bash
     cd your-repo-name
     ```

3. **设置虚拟环境（可选）**
   - 创建虚拟环境：
     ```bash
     python -m venv venv
     ```
   - 激活虚拟环境：
     - Linux/macOS 系统下：
       ```bash
       source venv/bin/activate
       ```
     - Windows 系统下：
       ```bash
       venv\Scripts\activate
       ```

4. **安装依赖**
   - 安装所需的包：
     ```bash
     pip install flask werkzeug
     ```

5. **运行应用**
   - 启动 Flask 服务器：
     ```bash
     python filesu_test.py
     ```

6. **访问应用**
   - 在浏览器中打开以下地址：
     ```
     http://0.0.0.0:5000
     ```
     或
     ```
     http://localhost:5000
     ```

7. **使用说明**
   - **目录导航：** 点击文件夹名称进入子目录。
   - **上传：** 使用“上传文件”或“上传文件夹”表单将新文件/文件夹添加到当前目录。
   - **下载：** 点击“下载”按钮下载文件；对于文件夹，系统会先压缩为 ZIP 文件再进行下载。
   - **管理：** 使用“重命名”和“删除”功能管理文件及文件夹。
   - **排序与分页：** 通过点击排序箭头和分页链接来控制显示效果。
