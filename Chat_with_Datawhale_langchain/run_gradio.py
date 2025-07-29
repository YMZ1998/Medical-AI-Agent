import re

import gradio as gr

from Chat_with_Datawhale_langchain.app_config import app_config
from database.create_db import create_db_info
from utils.call_llm import get_completion
from qa_chain.Chat_QA_chain_self import Chat_QA_chain_self
from qa_chain.QA_chain_self import QAChainSelf


class ModelCenter:
    """
    管理问答链对象：
    - chat_qa_chain_self: 支持历史记录的问答链
    - qa_chain_self: 不支持历史记录的问答链
    """

    def __init__(self):
        self.chat_qa_chain_self = {}
        self.qa_chain_self = {}

    def chat_qa_chain_self_answer(self, question: str, chat_history: list = [], model: str = "openai",
                                  embedding: str = "openai", temperature: float = 0.0, top_k: int = 4,
                                  history_len: int = 3, file_path: str = app_config.default_db_path,
                                  persist_path: str = app_config.default_persist_path):
        if not question:
            return "", chat_history
        try:
            print("model: ", model)
            key = (model, embedding)
            if key not in self.chat_qa_chain_self:
                self.chat_qa_chain_self[key] = Chat_QA_chain_self(
                    model=model,
                    temperature=temperature,
                    top_k=top_k,
                    chat_history=chat_history,
                    file_path=file_path,
                    persist_path=persist_path,
                    embedding=embedding
                )
            chain = self.chat_qa_chain_self[key]
            answer, _ = chain.answer(question, temperature, top_k)
            chat_history.append((question, answer))
            return "", chat_history
        except Exception as e:
            print("str(e): ", str(e))
            return str(e), chat_history

    def qa_chain_self_answer(self, question: str, chat_history: list = [], model: str = "openai", embedding="openai",
                             temperature: float = 0.0, top_k: int = 4, file_path: str = app_config.default_db_path,
                             persist_path: str = app_config.default_persist_path):
        if not question:
            return "", chat_history

        try:
            print("model: ", model)
            key = (model, embedding)
            if key not in self.qa_chain_self:
                self.qa_chain_self[key] = QAChainSelf(
                    model=model,
                    temperature=temperature,
                    top_k=top_k,
                    file_path=file_path,
                    persist_path=persist_path,
                    embedding=embedding
                )
            chain = self.qa_chain_self[key]
            chat_history.append((question, chain.answer(question, temperature, top_k)))
            return "", chat_history
        except Exception as e:
            return str(e), chat_history

    def clear_history(self):
        for chain in self.chat_qa_chain_self.values():
            chain.clear_history()


def format_chat_prompt(message, chat_history):
    prompt = ""
    for user_msg, bot_msg in chat_history:
        prompt += f"\nUser: {user_msg}\nAssistant: {bot_msg}"
    prompt += f"\nUser: {message}\nAssistant:"
    return prompt


def respond(message, chat_history, llm, history_len=3, temperature=0.1, max_tokens=2048):
    if not message:
        return "", chat_history
    try:
        chat_history = chat_history[-history_len:] if history_len > 0 else []

        prompt = format_chat_prompt(message, chat_history)

        bot_message = get_completion(prompt, llm, temperature=temperature, max_tokens=max_tokens)
        bot_message = re.sub(r"\\n", "<br/>", bot_message)

        chat_history.append((message, bot_message))

        # print("respond chat_history: ", chat_history)

        return "", chat_history

    except Exception as e:
        return str(e), chat_history


model_center = ModelCenter()

block = gr.Blocks()
with block as demo:
    with gr.Row(equal_height=True):
        gr.Image(value=app_config.aigc_logo_path, scale=1, min_width=10, show_label=False, show_download_button=False,
                 container=False)
        with gr.Column(scale=2):
            gr.Markdown("""<h1><center>Medical Assistant</center></h1><center>AI-Agent</center>""")
        gr.Image(value=app_config.datawhale_logo_path, scale=1, min_width=10, show_label=False,
                 show_download_button=False, container=False)

    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(height=900, show_copy_button=True, show_share_button=True,
                                 avatar_images=(app_config.aigc_logo_path, app_config.datawhale_avatar_path))
            msg = gr.Textbox(label="Prompt/问题")
            with gr.Row():
                db_with_his_btn = gr.Button("Chat db with history")
                db_wo_his_btn = gr.Button("Chat db without history")
                llm_btn = gr.Button("Chat with llm")
            with gr.Row():
                clear = gr.ClearButton(components=[chatbot], value="Clear console")

        with gr.Column(scale=1):
            file = gr.File(label='请选择知识库目录', file_count='directory',
                           file_types=['.txt', '.md', '.docx', '.pdf'])
            init_db = gr.Button("知识库文件向量化")

            with gr.Accordion("参数配置", open=False):
                temperature = gr.Slider(0, 1, value=0.01, step=0.01, label="llm temperature", interactive=True)
                top_k = gr.Slider(1, 10, value=3, step=1, label="vector db search top k", interactive=True)
                history_len = gr.Slider(0, 5, value=3, step=1, label="history length", interactive=True)

            with gr.Accordion("模型选择"):
                llm = gr.Dropdown(app_config.llm_model_list, label="large language model", value=app_config.init_llm,
                                  interactive=True)
                embeddings = gr.Dropdown(app_config.embedding_model_list, label="Embedding model",
                                         value=app_config.init_embedding_model)
            gr.Markdown("""
            提醒：<br>
            1. 使用时请先上传自己的知识文件，不然将会解析项目自带的知识库。<br>
            2. 初始化数据库时间可能较长，请耐心等待。<br>
            3. 使用中如果出现异常，将会在文本输入框进行展示，请不要惊慌。<br>
            """)
        init_db.click(create_db_info, inputs=[file, embeddings], outputs=[msg])
        db_with_his_btn.click(model_center.chat_qa_chain_self_answer,
                              inputs=[msg, chatbot, llm, embeddings, temperature, top_k, history_len],
                              outputs=[msg, chatbot])
        db_wo_his_btn.click(model_center.qa_chain_self_answer,
                            inputs=[msg, chatbot, llm, embeddings, temperature, top_k], outputs=[msg, chatbot])
        llm_btn.click(respond, inputs=[msg, chatbot, llm, history_len, temperature], outputs=[msg, chatbot])
        msg.submit(respond, inputs=[msg, chatbot, llm, history_len, temperature], outputs=[msg, chatbot])
        clear.click(model_center.clear_history)

gr.close_all()
demo.launch()
