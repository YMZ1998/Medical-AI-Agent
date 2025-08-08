import requests

from scripts.md_to_text import md_to_text

url = "http://localhost:9000/chat"
data = {
    "session_id": "u123",
    "question": "病人发烧三天该怎么办？",
    "template_type": "diagnosis",
    "context": "患者男性，35岁，发热伴咳嗽"
}
resp = requests.post(url, json=data)

resp_json = resp.json()
print(resp_json.get("answer", ""))
print(resp_json.get("chat_history", ""))
print(resp_json.get("elapsed_seconds", ""))

print(md_to_text(resp_json.get("answer", "")))
