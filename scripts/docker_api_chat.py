import requests

url = "http://localhost:8000/v1/chat/completions"
headers = {"Content-Type": "application/json"}

data = {
    "model": "Qwen/Qwen3-0.6B",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "请介绍一下Qwen模型。"}
    ],
    "max_tokens": 512,
    "temperature": 0.7,
}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(result["choices"][0]["message"]["content"])
