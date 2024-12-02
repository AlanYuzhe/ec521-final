import requests

# 登录和上传的 URL
base_url = "http://127.0.0.1:5000"
login_url = f"{base_url}/login"
upload_url = f"{base_url}/upload"

# 测试账号信息
test_username = "123"
test_password = "123"

# 文件路径
test_file_path = "test/test.txt"

# 创建一个会话对象，支持自动管理 Cookie
session = requests.Session()

# 步骤 1：模拟登录
login_payload = {
    "username": test_username,
    "password": test_password
}

login_response = session.post(login_url, data=login_payload)

# 检查登录结果
if "登录成功" in login_response.text:
    print("登录成功！")
else:
    print("登录失败！请检查用户名或密码。")
    print(f"服务器响应：{login_response.text}")
    exit()

# 步骤 2：上传文件（测试路径遍历漏洞）
try:
    with open(test_file_path, "rb") as file:
        files = {
            # 使用路径遍历的文件名
            "photo": ("../../etc/passwd", file)
        }
        upload_response = session.post(upload_url, files=files)

        # 输出服务器响应结果
        print("服务器响应：")
        print(upload_response.text)

        # 检查响应结果是否包含意外行为
        if "成功" in upload_response.text:
            print("上传成功，但需要检查路径遍历是否被利用。")
        else:
            print("上传失败，路径遍历可能已被防护。")
except FileNotFoundError:
    print(f"测试文件未找到，请检查路径是否正确：{test_file_path}")
