import os
import gradio as gr
from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

from api_config import api_config

api_key = api_config.get_api_key()

llm = ChatTongyi(
    dashscope_api_key=api_key,
    model="qwen-turbo",
    temperature=0.3,
) | StrOutputParser()

chat_history = [SystemMessage(content="You are a helpful financial assistant named Joey.")]


def chat_interface(user_input, history):
    print("User:", user_input)
    chat_history.append(HumanMessage(content=user_input))
    response = llm.invoke(chat_history)
    chat_history.append(AIMessage(content=response))
    history.append((user_input, response))
    print("AI:", response)
    return history, history, ""  # 返回 history、state、清空输入框


with gr.Blocks() as demo:
    gr.Markdown("## 🧑‍💼 金融助手 Joey")

    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="请输入您的问题", placeholder="例如：有什么好的投资建议？", lines=1)
    send = gr.Button("发送")
    clear = gr.Button("清除对话")

    state = gr.State([])

    msg.submit(chat_interface, [msg, state], [chatbot, state, msg])
    send.click(chat_interface, [msg, state], [chatbot, state, msg])


    def reset_chat():
        chat_history.clear()
        chat_history.append(SystemMessage(content="You are a helpful financial assistant named Joey."))
        return [], []


    clear.click(reset_chat, None, [chatbot, state])

if __name__ == "__main__":
    demo.launch(share=True, server_port=7862, debug=True)
