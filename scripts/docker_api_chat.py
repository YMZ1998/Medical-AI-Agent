import requests
import time

# url = "http://localhost:8000/v1/chat/completions"
url = "http://192.168.0.90:8000/v1/chat/completions"
headers = {"Content-Type": "application/json"}

messages = [
    {"role": "system", "content": "You are a helpful assistant."}
]


def chat_with_model(user_input):
    messages.append({"role": "user", "content": user_input})
    chat = messages[-2:]
    data = {
        "model": "doctor",
        "messages": chat,
        "max_tokens": 512,
        "temperature": 0.7,
    }

    start_time = time.time()
    response = requests.post(url, json=data, headers=headers)
    elapsed = time.time() - start_time

    response.raise_for_status()
    result = response.json()

    assistant_msg = result["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": assistant_msg})

    print(f"[耗时 {elapsed:.2f} 秒]")
    print("Assistant:", assistant_msg)


if __name__ == "__main__":
    print("开始对话（输入 exit 退出）")
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("结束对话。")
            break
        if user_input == "":
            continue
        chat_with_model(user_input)
