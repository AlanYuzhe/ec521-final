import requests

url = "http://127.0.0.1:5000/upload"
files = {
    "photo": ("../test.txt", open("test/test.txt", "rb"))
}

response = requests.post(url, files=files)

print(response.text)
