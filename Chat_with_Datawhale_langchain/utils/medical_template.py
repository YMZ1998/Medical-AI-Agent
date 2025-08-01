from langchain.prompts import PromptTemplate

from Chat_with_Datawhale_langchain.utils.template import medical_templates


class MedicalPromptBuilder:
    def __init__(self, template_dict: dict, mode: str = "general"):
        self.template = template_dict.get(mode)
        if not self.template:
            raise ValueError(f"未找到名为 '{mode}' 的模板")
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template=self.template
        )
        self.chat_history = []

    def set_chat_history(self, history: list):
        self.chat_history = history

    def add_history(self, question: str, answer: str):
        self.chat_history.append((question.strip(), answer.strip()))

    def clear_history(self):
        self.chat_history = []

    def build_prompt(self, question: str) -> str:
        context_str = "\n".join([f"用户: {q}\n助手: {a}" for q, a in self.chat_history])
        return self.prompt_template.format(context=context_str.strip(), question=question.strip())


# 使用示例
if __name__ == "__main__":
    builder = MedicalPromptBuilder(medical_templates, mode="general")
    chat_history = [
        ("最近老是咳嗽", "可能是慢性咽炎，也可能是过敏引起的，建议进一步检查。"),
        ("我有点怕去医院", "可以先做基础体检，也可以通过线上问诊初步评估。")
    ]
    builder.set_chat_history(chat_history)
    # builder.add_history("最近老是咳嗽", "可能是慢性咽炎，也可能是过敏引起的，建议进一步检查。")
    # builder.add_history("我有点怕去医院", "可以先做基础体检，也可以通过线上问诊初步评估。")

    final_prompt = builder.build_prompt("怎么提高抵抗力？")
    print(final_prompt)
