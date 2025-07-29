import os
from Chat_with_Datawhale_langchain.database.create_db import create_db, load_knowledge_db
from Chat_with_Datawhale_langchain.embedding.call_embedding import get_embedding

def get_vectordb(
    file_path: str = None,
    persist_path: str = None,
    embedding: str = "openai",
    embedding_key: str = None,
    update: bool = False
):
    """
    创建并返回向量数据库对象

    参数:
        file_path: 文本文件路径，用于创建数据库（首次或目录为空时）
        persist_path: 向量数据库持久化路径
        embedding: 使用的嵌入模型（默认 "openai"）
        embedding_key: 嵌入模型的 API 密钥
        update: 是否强制更新数据库（默认 False）

    返回:
        vectordb: 向量数据库对象
    """
    print("正在创建/加载向量数据库...")
    print(f"file_path: {file_path}")
    print(f"persist_path: {persist_path}")
    print(f"是否强制更新: {update}")

    # 获取 embedding 对象
    embedding = get_embedding(embedding=embedding, embedding_key=embedding_key)

    if not persist_path:
        raise ValueError("persist_path 不可为空，请指定向量数据库的存储路径。")

    need_create = update or not os.path.exists(persist_path) or not os.listdir(persist_path)

    if need_create:
        if not file_path or not os.path.exists(file_path):
            raise ValueError("file_path 无效或不存在，无法创建新向量数据库。")
        print("创建新的向量数据库...")
        create_db(file_path, persist_path, embedding)
    else:
        print("加载已有向量数据库...")

    # 加载向量数据库
    vectordb = load_knowledge_db(persist_path, embedding)

    print("向量数据库准备完成。")
    return vectordb
