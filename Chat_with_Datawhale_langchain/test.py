import requests

url = "http://127.0.0.1:8000/chat"

chat_history = []


def chat_with_bot(question):
    data = {
        "question": question,
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        answer = response.json().get("response", "")
        chat_history.append(("User", question))
        chat_history.append(("Bot", answer))
        return answer
    else:
        return f"请求失败，状态码：{response.status_code}"


questions = [
    "你好，请问你是谁？",
    "怎么提高抵抗力？",
    "有什么简单的锻炼方法？"
]

for q in questions:
    print(f"User: {q}")
    ans = chat_with_bot(q)
    print(f"Bot: {ans}")
    print("-" * 30)
