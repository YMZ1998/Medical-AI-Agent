import datetime
import os
from http import HTTPStatus

import gradio as gr
from dashscope import Application

from api_config import api_config

dashscope_api_key = api_config.get_api_key()
app_id = os.getenv("DASHSCOPE_APP_ID")
session_id = None  # 初始无会话


def log_chat(user_input, assistant_reply):
    log_file = "chat_log.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}]\n用户: {user_input}\n助手: {assistant_reply}\n{'-' * 40}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    print(log_entry)


def dashscope_chat(user_input, chat_history=[]):
    global session_id

    call_params = {
        "api_key": dashscope_api_key,
        "app_id": app_id,
        "prompt": user_input
    }

    if session_id:
        call_params["session_id"] = session_id

    response = Application.call(**call_params)

    if response.status_code != HTTPStatus.OK:
        error_message = f"[错误] code={response.status_code}, message={response.message}"
        log_chat(user_input, error_message)
        return chat_history + [[user_input, error_message]], ""

    session_id = response.output.session_id
    assistant_reply = response.output.text

    log_chat(user_input, assistant_reply)

    chat_history.append([user_input, assistant_reply])
    return chat_history, ""


def clear_chat():
    global session_id
    session_id = None
    return [], "", None


with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Stock God 聊天助手", elem_classes="title")

    chatbot = gr.Chatbot(label="对话窗口", height=400)

    with gr.Row():
        msg = gr.Textbox(
            show_label=False,
            placeholder="请输入问题，例如：你是谁？",
            scale=8
        )
        send_btn = gr.Button("发送", variant="primary", scale=1)

    clear_btn = gr.Button("🗑️ 清除会话", variant="secondary")

    msg.submit(dashscope_chat, [msg, chatbot], [chatbot, msg])
    send_btn.click(dashscope_chat, [msg, chatbot], [chatbot, msg])
    clear_btn.click(clear_chat, None, [chatbot, msg])

if __name__ == "__main__":
    demo.launch(share=True, server_port=7862, debug=True)
