import os
import re
import tempfile

from langchain.document_loaders import PyMuPDFLoader
from langchain.document_loaders import UnstructuredFileLoader
from langchain.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

from API import api_config
from Chat_with_Datawhale_langchain.embedding.call_embedding import get_embedding

dashscope_api_key = api_config.get_api_key()

DEFAULT_DB_PATH = "../knowledge_db"
DEFAULT_PERSIST_PATH = "./vector_db"


def get_files(dir_path):
    file_list = []
    for filepath, dirnames, filenames in os.walk(dir_path):
        for filename in filenames:
            file_list.append(os.path.join(filepath, filename))
    return file_list


def file_loader(file, loaders):
    if isinstance(file, tempfile._TemporaryFileWrapper):
        file = file.name
    if not os.path.isfile(file):
        [file_loader(os.path.join(file, f), loaders) for f in  os.listdir(file)]
        return
    file_type = file.split('.')[-1]
    if file_type == 'pdf':
        loaders.append(PyMuPDFLoader(file))
    elif file_type == 'md':
        pattern = r"不存在|风控"
        match = re.search(pattern, file)
        if not match:
            loaders.append(UnstructuredMarkdownLoader(file))
    elif file_type == 'txt':
        loaders.append(UnstructuredFileLoader(file))
    return


def create_db_info(files=DEFAULT_DB_PATH, embeddings="openai", persist_directory=DEFAULT_PERSIST_PATH):
    print("create db info")
    if embeddings == 'openai' or embeddings == 'm3e' or embeddings =='tongyi':
        vectordb = create_db(files, persist_directory, embeddings)
    else:
        print("embedding model not support")
    return ""


def create_db(files=DEFAULT_DB_PATH,
              persist_directory=DEFAULT_PERSIST_PATH,
              embeddings="openai"):
    """
    加载 PDF 文件，切分文档，生成嵌入向量，创建 Chroma 向量数据库。

    参数:
        files (str or List[str]): 文件路径或路径列表
        persist_directory (str): 向量数据库持久化路径
        embeddings (str or Embeddings): 嵌入模型名称或对象

    返回:
        Chroma: 构建完成的向量数据库对象
    """
    if not files:
        return "can't load empty file"
    if isinstance(files, str):
        files = [files]

    # 文档加载
    loaders = []
    for file in files:
        file_loader(file, loaders)

    docs = []
    for loader in loaders:
        if loader is not None:
            docs.extend(loader.load())

    if not docs:
        raise ValueError("未能加载任何文档，请检查文件路径或文件格式")

    # 文本切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=150
    )
    split_docs = text_splitter.split_documents(docs)

    # 加载 Embedding 模型
    if isinstance(embeddings, str):
        embeddings = get_embedding(embedding=embeddings)

    # 如果使用 Tongyi，则自动做 batch 处理（<=10）
    if hasattr(embeddings, "embed_documents"):
        orig_embed_documents = embeddings.embed_documents

        def batch_safe_embed_documents(texts):
            batch_size = 10
            results = []
            for i in range(0, len(texts), batch_size):
                results += orig_embed_documents(texts[i:i + batch_size])
            return results

        embeddings.embed_documents = batch_safe_embed_documents

    # 创建向量数据库
    vectordb = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectordb.persist()

    return vectordb


def presit_knowledge_db(vectordb):
    """
    该函数用于持久化向量数据库。

    参数:
    vectordb: 要持久化的向量数据库。
    """
    vectordb.persist()


def load_knowledge_db(path, embeddings):
    """
    该函数用于加载向量数据库。

    参数:
    path: 要加载的向量数据库路径。
    embeddings: 向量数据库使用的 embedding 模型。

    返回:
    vectordb: 加载的数据库。
    """
    vectordb = Chroma(
        persist_directory=path,
        embedding_function=embeddings
    )
    return vectordb


if __name__ == "__main__":
    create_db(embeddings="tongyi")
