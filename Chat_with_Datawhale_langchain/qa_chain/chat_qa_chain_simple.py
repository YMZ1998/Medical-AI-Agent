import re

from Chat_with_Datawhale_langchain.qa_chain.model_to_llm import model_to_llm
from Chat_with_Datawhale_langchain.utils.medical_template import MedicalPromptBuilder

from Chat_with_Datawhale_langchain.utils.template import medical_templates, DEFAULT_TEMPLATE


class Chat_QA_chain_simple:
    def __init__(self, model: str, use_history: bool = False, temperature: float = 0.0, chat_history: list = None,
                 api_key: str = None,
                 template: str = None):
        self.model = model
        self.temperature = temperature
        self.use_history = use_history
        self.chat_history = chat_history or []
        self.api_key = api_key
        self.template = template or DEFAULT_TEMPLATE

    def clear_history(self):
        self.chat_history.clear()

    def change_history_length(self, history_len: int = 1):
        return self.chat_history[-history_len:]

    def format_prompt(self, question: str) -> str:
        """将模板填充为最终提示词"""
        builder = MedicalPromptBuilder(medical_templates, mode="general")
        if self.use_history:
            for q, a in self.chat_history:
                builder.add_history(q, a)

        context_prompt = builder.build_prompt(question)
        # print("context_prompt: ", context_prompt)
        return context_prompt

    def answer(self, question: str = None, temperature=None):
        if not question:
            return "", self.chat_history

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

    mode = "general"  # 可选 "general", "vulnerable", "diagnosis"
    chatbot = Chat_QA_chain_simple(
        model="qwen-turbo",
        use_history=False,
        api_key=dashscope_api_key,
        template=medical_templates.get(mode)
    )

    questions = [
        "你好，你有什么技能？",
        "怎么提高抵抗力？",
        "什么是高血压的初期表现？"
    ]

    for question in questions:
        print(f"用户: {question}")
        answer, history = chatbot.answer(question)
        print(f"助手: {answer}")
        # print(f"历史记录: {history}")
        print("-" * 50)
