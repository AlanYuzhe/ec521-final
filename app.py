import os
import filetype
from flask import Flask, request, redirect, url_for, flash, render_template

from flask import send_file
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
    UserMixin,
)
from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 分钟
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 上传文件的根目录
app.config['UPLOAD_FOLDER'] = 'uploads'
# 设置允许的最大文件大小（16MB）
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 创建根目录
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'user'  # 默认注册为普通用户

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful, please log in...')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful。')
            return redirect(url_for('upload'))
        else:
            flash('Wrong username or password!')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You are logged out！')
    return redirect(url_for('login'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    # 为当前用户创建上传目录
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    if request.method == 'POST' and 'photo' in request.files:
        file = request.files['photo']

        if file.filename == '':
            flash('No file selected!')
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
                    flash('Unable to determine the file type!')
                    return redirect(request.url)

            # 验证 MIME 类型是否允许
            if kind_mime not in ['image/jpeg', 'image/png', 'text/plain']:
                flash('Disallowed file types!')
                return redirect(request.url)

        except Exception as e:
            flash(f'Unable to determine file type：{str(e)}')
            return redirect(request.url)

        # 使用 UUID 生成唯一的文件名，防止文件名冲突
        import uuid

        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"

        # 保存文件到用户的专属目录
        save_path = os.path.join(user_folder, unique_filename)
        try:
            file.save(save_path)

            # 病毒扫描（可选）
            # scan_result = scan_file(save_path)
            # if scan_result is not None:
            #     # 如果发现病毒，删除文件并提示用户
            #     os.remove(save_path)
            #     flash('上传的文件包含病毒，已被删除。')
            #     return redirect(url_for('upload'))

            flash(f'File {original_filename} uploaded successfully。')
        except Exception as e:
            flash(f'Upload failed：{str(e)}')

        return redirect(url_for('upload'))

    return render_template('upload.html')


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash('Upload failed: The file is too large. The maximum allowed size is 16MB!')
    return redirect(url_for('upload'))


@app.route('/view_file/<username>/<filename>')
@login_required
def view_file(username, filename):
    # 检查用户权限
    if current_user.role == 'admin' or current_user.username == username:
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        file_path = os.path.join(user_folder, filename)
        if not os.path.isfile(file_path):
            return "File not found。"
    else:
        return "No permission to access the file!"

    # 检测文件类型
    mime_type = filetype.guess_mime(file_path)
    if mime_type and mime_type.startswith('image/'):
        # 如果是图片文件，通过 send_file 返回图片供浏览器显示
        return send_file(file_path, mimetype=mime_type)

    # 如果是其他类型文件，显示为文本（如原来的逻辑）
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return f"<pre>{content}</pre>"
    except Exception as e:
        return f"Unable to read file：{str(e)}"


@app.route('/my_files')
@login_required
def my_files():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    if not os.path.exists(user_folder):
        files = []
    else:
        files = os.listdir(user_folder)
    return render_template('my_files.html', files=files, username=current_user.username)


@app.route('/all_files')
@login_required
def all_files():
    if current_user.role != 'admin':
        flash('No access!')
        return redirect(url_for('upload'))

    all_files = {}
    for user_dir in os.listdir(app.config['UPLOAD_FOLDER']):
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user_dir)
        if os.path.isdir(user_folder):
            files = os.listdir(user_folder)
            all_files[user_dir] = files

    return render_template('all_files.html', all_files=all_files)


if __name__ == "__main__":
    app.run(
        debug=True,
        ssl_context=('cert.pem', 'key.pem')  # 启用 HTTPS
    )

