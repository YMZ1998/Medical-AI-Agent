import os
from http import HTTPStatus
import gradio as gr
from dashscope import Application
from API import get_dashscope_api_key

dashscope_api_key = get_dashscope_api_key()
app_id = '375f8ed21d9746838e92924a5bf24fc9'
session_id = None

def dashscope_chat(user_input, chat_history=[]):
    global session_id

    # 构建调用参数
    call_params = {
        "api_key": dashscope_api_key,
        "app_id": app_id,
        "prompt": user_input
    }

    # 若已有会话 ID，则追加进去以保持上下文
    if session_id:
        call_params["session_id"] = session_id

    # 调用 DashScope 应用
    response = Application.call(**call_params)

    # 错误处理
    if response.status_code != HTTPStatus.OK:
        error_message = f"[错误] code={response.status_code}, message={response.message}"
        return chat_history + [[user_input, error_message]], ""

    # 更新会话 ID
    session_id = response.output.session_id

    # 获取返回结果
    assistant_reply = response.output.text

    # 更新聊天历史
    chat_history.append([user_input, assistant_reply])
    return chat_history, ""


# Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("# Stock God")
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="请输入问题", placeholder="例如：你是谁？")
    clear = gr.Button("清除会话")

    # 发送输入事件
    msg.submit(dashscope_chat, [msg, chatbot], [chatbot, msg])
    clear.click(lambda: ([], "", None), None, [chatbot, msg])

if __name__ == "__main__":
    demo.launch(share=True, server_port=7862, debug=True)
