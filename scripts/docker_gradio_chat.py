import gradio as gr
import requests
import time

# vLLM 服务地址（局域网内）
url = "http://192.168.0.90:8000/v1/chat/completions"
headers = {"Content-Type": "application/json"}

# 初始对话上下文
messages = [
    {"role": "system", "content": "You are a helpful medical assistant."}
]

# 聊天函数：处理每次用户输入
def chat_fn(user_input, chat_history):
    messages.append({"role": "user", "content": user_input})
    # 使用最近一轮对话（保留上下文更长可自定义）
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

    result = response.json()
    assistant_msg = result["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": assistant_msg})

    # 添加到 Gradio 聊天历史
    chat_history.append((user_input, f"{assistant_msg}  \n\n⏱️ 耗时：{elapsed:.2f} 秒"))
    return "", chat_history

# 重置函数
def clear_chat():
    global messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    return [], ""

# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("# 聊天助手")
    chatbot = gr.Chatbot(label="Assistant", height=800)
    msg = gr.Textbox(label="你的问题", placeholder="输入后按回车", lines=1)
    clear = gr.Button("清除对话")

    msg.submit(chat_fn, [msg, chatbot], [msg, chatbot])
    clear.click(fn=clear_chat, outputs=[chatbot, msg])

# 启动服务（在浏览器打开）
demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
