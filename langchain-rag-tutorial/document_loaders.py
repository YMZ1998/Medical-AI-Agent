from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_community.chat_models import ChatTongyi
from API import get_dashscope_api_key
import os

# 1. 获取通义千问 API key
dashscope_api_key = get_dashscope_api_key()

# 2. 加载英文文档
loader = TextLoader("./data/books/test.md", encoding="utf-8")
docs = loader.load()

# 3. 初始化模型
model = ChatTongyi(dashscope_api_key=dashscope_api_key)


# 4. 翻译函数
def translate_text(text: str) -> str:
    resp = model.invoke(f"请把下面英文翻译成中文：\n\n{text}")
    return resp.content.strip()


# 5. 翻译并对照保存
output_lines = []
for i, doc in enumerate(docs):
    original = doc.page_content.strip()
    if not original:
        continue  # 跳过空行
    translated = translate_text(original)

    # 拼接对照内容
    output_lines.append(f"[段落 {i + 1} 英文]:\n{original}\n")
    output_lines.append(f"[段落 {i + 1} 中文]:\n{translated}\n")
    output_lines.append("-" * 50 + "\n")

# 6. 写入对照结果文件
output_path = "./data/books/test_translated.md"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.writelines(output_lines)

print(f"\n✅ 对照翻译完成，已保存至: {output_path}")
