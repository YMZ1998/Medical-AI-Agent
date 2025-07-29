import os

from langchain_community.chat_models import ChatTongyi
from langchain_community.document_loaders import TextLoader

from api_config import api_config

dashscope_api_key = api_config.get_api_key()

loader = TextLoader("./data/test.md", encoding="utf-8")
docs = loader.load()
print(docs)

# loader = PyPDFLoader("./data/test.pdf")
# docs = loader.load()
# print(docs)

model = ChatTongyi(dashscope_api_key=dashscope_api_key)


def translate_text(text: str) -> str:
    resp = model.invoke(f"请把下面英文翻译成中文：\n\n{text}")
    return resp.content.strip()


output_lines = []
for i, doc in enumerate(docs):
    original = doc.page_content.strip()
    print(f"[{i + 1}/{len(docs)}] 原文：{original}")
    if not original:
        continue  # 跳过空行
    translated = translate_text(original)
    print(f"[{i + 1}/{len(docs)}] 翻译：{translated}")

    output_lines.append(f"{original}\n\n")
    output_lines.append(f"---\n\n{translated}\n\n")

output_path = "./data/test_translated.md"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.writelines(output_lines)

print(f"\n✅ 对照翻译完成，已保存至: {output_path}")
