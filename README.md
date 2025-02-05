# File Management System 

[中文版本](README_zh.md) | [English Version](README.md)

This repository contains a file management system built using Python and Flask. It offers a web interface for uploading, downloading (folders are compressed into ZIP files before download), renaming, and deleting files and folders. Additional features include sorting, pagination, and search.

## Step-by-Step Instructions

1. **Clone the Repository**
   - Open your terminal and run:
     ```bash
     git clone https://github.com/yourusername/your-repo-name.git
     ```
   - (Please replace the URL with your actual repository URL)

2. **Navigate to the Project Directory**
   - Change directory into the repository:
     ```bash
     cd your-repo-name
     ```

3. **Set Up a Virtual Environment (Optional)**
   - Create a virtual environment:
     ```bash
     python -m venv venv
     ```
   - Activate the virtual environment:
     - On Linux/macOS:
       ```bash
       source venv/bin/activate
       ```
     - On Windows:
       ```bash
       venv\Scripts\activate
       ```

4. **Install Dependencies**
   - Install the required packages:
     ```bash
     pip install flask werkzeug
     ```

5. **Run the Application**
   - Start the Flask server by running:
     ```bash
     python filesu_test.py
     ```

6. **Access the Application**
   - Open your web browser and go to:
     ```
     http://0.0.0.0:5000
     ```
     or
     ```
     http://localhost:5000
     ```

7. **Usage**
   - **Navigation:** Click on folder names to navigate into subdirectories.
   - **Uploading:** Use the "Upload File" or "Upload Folder" forms to add new items to the current directory.
   - **Downloading:** Click the "Download" button to download files; folders will be compressed into ZIP archives before download.
   - **Managing:** Use the "Rename" and "Delete" options to manage files and folders.
   - **Sorting & Pagination:** Use the provided sorting buttons and pagination links to control the display.
