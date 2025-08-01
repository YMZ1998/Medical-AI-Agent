import re
import os
from datetime import datetime

from Chat_with_Datawhale_langchain.qa_chain.model_to_llm import model_to_llm
from Chat_with_Datawhale_langchain.utils.medical_template import MedicalPromptBuilder
from Chat_with_Datawhale_langchain.utils.template import medical_templates, DEFAULT_TEMPLATE


class Chat_QA_chain_simple:
    def __init__(self, model: str, use_history: bool = False, temperature: float = 0.0, chat_history: list = None,
                 api_key: str = None, template: str = None):
        self.model = model
        self.temperature = temperature
        self.use_history = use_history
        self.chat_history = chat_history or []
        self.api_key = api_key
        self.template = template or DEFAULT_TEMPLATE
        self.dir_path = "chat_logs"

    def clear_history(self):
        self.chat_history.clear()

    def change_history_length(self, history_len: int = 1):
        return self.chat_history[-history_len:]

    def format_prompt(self, question: str) -> str:
        """将模板填充为最终提示词"""
        builder = MedicalPromptBuilder(medical_templates, mode="general")
        if self.use_history:
            builder.set_chat_history(self.chat_history)

        context_prompt = builder.build_prompt(question)
        return context_prompt

    def save_history_to_md(self):
        """保存对话到 markdown 文件"""
        os.makedirs(self.dir_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.md"
        filepath = os.path.join(self.dir_path, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# 医疗对话记录\n\n")
            for idx, (q, a) in enumerate(self.chat_history, 1):
                f.write(f"### 问题 {idx}：{q}\n\n")
                f.write(f"**回答：** {a}\n\n")

        return filepath

    def answer(self, question: str = None, temperature=None):
        if not question:
            return "", self.chat_history

        # 触发 MCP 保存指令
        if question.strip() in ["保存对话", "保存记录", "保存聊天"]:
            file_path = self.save_history_to_md()
            return f"✅ 对话已保存至：`{file_path}`", self.chat_history

        temperature = temperature if temperature is not None else self.temperature
        llm = model_to_llm(self.model, temperature, self.api_key)

        response = llm.invoke(self.format_prompt(question))
        answer = getattr(response, "content", str(response)).strip()
        answer = re.sub(r"\\n", '<br/>', answer)

        self.chat_history.append((question, answer))
        return answer, self.chat_history


if __name__ == '__main__':
    from api_config import api_config

    dashscope_api_key = api_config.get_api_key()

    mode = "general"
    chatbot = Chat_QA_chain_simple(
        model="qwen-turbo",
        use_history=True,
        api_key=dashscope_api_key,
        template=medical_templates.get(mode)
    )

    questions = [
        "你好，你有什么技能？，保存对话",
        # "怎么提高抵抗力？",
        # "什么是高血压的初期表现？",
        "保存对话啊"  # 🔥 触发 MCP 保存
    ]

    for question in questions:
        print(f"用户: {question}")
        answer, history = chatbot.answer(question)
        print(f"助手: {answer}")
        print("-" * 50)
