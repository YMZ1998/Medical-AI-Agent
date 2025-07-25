import argparse
import os

from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_community.vectorstores import Chroma
from embeddings import TongyiEmbeddings

from API import get_dashscope_api_key

dashscope_api_key = get_dashscope_api_key()

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", nargs="?", help="The query text.")
    args = parser.parse_args()
    args.query_text = "What does the cat do in the morning?"
    if args.query_text is None:
        query_text = input("请输入你要查询的问题：")
    else:
        query_text = args.query_text

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

    # 初始化 Embedding 和向量数据库
    embedding_function = TongyiEmbeddings(dashscope_api_key=api_key)
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_function,
        collection_metadata={"hnsw:space": "cosine"}  # 指定使用 cosine 距离
    )

    try:
        results = db.similarity_search_with_relevance_scores(query_text, k=3)
    except Exception as e:
        print(f"向量搜索失败：{e}")
        return

    print(results)
    score = results[0][1]
    # if score is None or score < 0.7:
    #     print(f"匹配度过低，得分：{score}")
    #     return

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    print(f"\n构造的提示语：\n{prompt}\n")

    try:
        model = ChatTongyi(dashscope_api_key=api_key)
        response = model.invoke(prompt)
        response_text = response.content
    except Exception as e:
        print(f"调用通义模型失败：{e}")
        return

    sources = [doc.metadata.get("source", "未知") for doc, _ in results]
    print(f"\n🧠 回答内容：{response_text}")
    print(f"\n📚 来源文档：{sources}")


if __name__ == "__main__":
    main()
