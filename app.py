import filetype
from flask import Flask, request, redirect, url_for, flash, render_template
from flask_uploads import UploadSet, configure_uploads, IMAGES, TEXT, patch_request_class
import os
from flask_uploads import UploadNotAllowed
import traceback
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'

app.config['UPLOADED_FILES_DEST'] = 'uploads'  
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

files = UploadSet('files', IMAGES + TEXT)

configure_uploads(app, files)

@app.route('/')
def index():
    return '<h1>Welcome to the Home Page!</h1>'

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        file = request.files['photo']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        original_filename = secure_filename(file.filename)

        try:
            # 读取文件内容
            content = file.read(1024)
            file.seek(0)  # 重置文件指针

            # 判断是否为文本文件
            try:
                content.decode('utf-8')  # 尝试将内容以 UTF-8 编码解码
                is_text_file = True
            except UnicodeDecodeError:
                is_text_file = False

            # 验证文件的扩展名和内容是否匹配文本文件
            if original_filename.lower().endswith('.txt') and is_text_file:
                kind_mime = 'text/plain'
            else:
                # 检测其他文件类型
                kind = filetype.guess(content)
                if kind:
                    kind_mime = kind.mime
                else:
                    flash('Cannot determine the file type.')
                    return redirect(request.url)

            # 验证 MIME 类型是否允许
            if kind_mime not in ['image/jpeg', 'image/png', 'text/plain']:
                flash('File type not allowed.')
                return redirect(request.url)

        except Exception as e:
            flash(f'Failed to determine file type: {str(e)}')
            return redirect(request.url)

        try:
            filename = files.save(file, name=original_filename)
            flash(f'File {filename} uploaded successfully.')
        except Exception as e:
            flash(f'Upload failed: {str(e)}')

        return redirect(url_for('upload'))

    return render_template('upload.html')


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash('Upload failed: The file is too large. Maximum size is 16MB.')
    return redirect(url_for('upload'))

@app.route('/view_file/<filename>')
def view_file(filename):
    file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], filename)
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return f"<pre>{content}</pre>"
    except Exception as e:
        return f"Could not read the file: {str(e)}"

if __name__ == "__main__":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
