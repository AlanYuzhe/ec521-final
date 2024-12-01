import requests

url = "http://localhost:5000/upload"
files = {
    "photo": ("../test.txt", open("test/test.txt", "rb"))
}

response = requests.post(url, files=files)

print(response.text)
