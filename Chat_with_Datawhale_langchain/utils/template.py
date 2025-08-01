DEFAULT_TEMPLATE = """
你是一个专业问答助手JOEY，请根据以下提供的上下文简明准确地回答用户问题。

- 如果无法从上下文中找到答案，请直接说“我不知道”，不要编造内容。
- 语言简洁清晰，逻辑通顺。

上下文：
{context}

问题：
{question}

回答：
"""

medical_templates = {
    "general": """
上下文：
{context}

作为一名专业的医学顾问 Kim，请就患者提出的问题 "{question}" 做出回答：
- 语言简洁清晰，逻辑通顺。不要回答无关内容。
- 若问题是医学相关的，则按以下要求回答，基于循证医学和当前指南，提供全面、准确且易于理解的医学建议。

""",

    "diagnosis": """
{context}
请作为一位经验丰富的临床医生，围绕 "{question}"，提供详细的诊断思路。
请涵盖：典型症状和体征、实验室检查、影像学检查、常用筛查方法和必要时的专科检查。
同时提供常见误诊原因以及排除方法。
""",

    "drug": """
{context}
针对主题 "{question}"，请提供当前推荐的一线和二线药物治疗方案。
请详细列出药物名称（通用名与商品名）、推荐剂量、给药方式、常见副作用及禁忌症。
若涉及慢性病或长期用药，请说明疗程及监测要点。
"""
}

# 模板元信息列表（用于菜单/选择框/描述等）
medical_template_list = [
    {
        "mode": "general",
        "name": "通用医学建议",
        "description": "全面覆盖病因、症状、诊断、治疗及预后等医学信息，适用于一般健康问题。"
    },
    {
        "mode": "diagnosis",
        "name": "临床诊断指导",
        "description": "提供系统性的诊断流程、鉴别思路和常见误诊风险，适用于诊断分析任务。"
    },
    {
        "mode": "drug",
        "name": "药物治疗推荐",
        "description": "详细列出适用药物名称、剂量、用法和不良反应，适用于药物相关问询。"
    },
    {
        "mode": "visit",
        "name": "就医与检查建议",
        "description": "判断是否需要就医及应进行的初步检查，适用于分诊类问题。"
    },
    {
        "mode": "chronic",
        "name": "慢性病管理",
        "description": "聚焦慢病监测、行为干预和长期用药管理，适用于如高血压、糖尿病等疾病。"
    },
    {
        "mode": "vulnerable",
        "name": "儿童/老年人特别建议",
        "description": "根据脆弱人群的生理特点调整医学建议，适用于儿科或老年病学场景。"
    },
    {
        "mode": "emergency",
        "name": "急诊/重症处理",
        "description": "用于紧急症状或危重情况的初步评估与应急处理指导。"
    }
]


def generate_medical_prompt(question: str, mode: str = "general", context: str = "") -> str:
    prompt_template = medical_templates.get(mode)
    if not prompt_template:
        raise ValueError(f"Unsupported mode: {mode}")

    context_block = f"【患者背景】：{context}\n" if context.strip() else ""

    prompt = prompt_template.replace("{question}", question).replace("{context}", context_block)
    return prompt


if __name__ == "__main__":
    # prompt = generate_medical_prompt(
    #     question="高血压",
    #     mode="chronic",
    #     context="患者为65岁男性，BMI为28，有糖尿病家族史，服药依从性差，血压波动较大"
    # )
    # print("生成的 Prompt:\n", prompt)
    #
    # vulnerable_item = next(item for item in medical_template_list if item["mode"] == "vulnerable")
    # print("\n模板信息:\n", vulnerable_item)

    from langchain.prompts import PromptTemplate

    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template=medical_templates.get("general")
    )

    # 假设有历史对话
    chat_history = [
        ("最近老是咳嗽", "可能是慢性咽炎，也可能是过敏引起的，建议进一步检查。"),
        ("我有点怕去医院", "可以先做基础体检，也可以通过线上问诊初步评估。")
    ]

    # 构造 context（历史对话）
    context_str = ""
    for q, a in chat_history:
        context_str += f"用户: {q}\n助手: {a}\n"

    # 构造最终 prompt
    final_prompt = prompt_template.format(context=context_str.strip(), question="怎么提高抵抗力？")
    print(final_prompt)

