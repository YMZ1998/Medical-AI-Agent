import requests

url = "http://127.0.0.1:8000/chat"

chat_history = []


def chat_with_bot(question):
    data = {
        "question": question,
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        resp_data = response.json().get("response", "")

        print(resp_data)

        if isinstance(resp_data, list):
            answer = resp_data[0]
        else:
            answer = str(resp_data)

        chat_history.append(("User", question))
        chat_history.append(("Bot", answer))
        return answer
    else:
        return f"请求失败，状态码：{response.status_code}"


questions = [
    "你好，你有什么技能？",
    "怎么提高抵抗力？",
    "有什么简单的锻炼方法？",
    # "这是一个什么故事？"
]

for q in questions:
    print(f"User: {q}")
    ans = chat_with_bot(q)
    print(f"Bot: {ans}")
    print("-" * 30)
