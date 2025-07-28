import requests

url = "http://127.0.0.1:5862"

data = {
    "prompt": "你是谁？",
    "api_key": ""
}

r = requests.post(url, json=data)

print(r)
