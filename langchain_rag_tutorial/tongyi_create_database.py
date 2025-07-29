import os
import shutil
from pathlib import Path

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma

from api_config import api_config
from embeddings import TongyiEmbeddings

dashscope_api_key = api_config.get_api_key()

CHROMA_PATH = "chroma"
DATA_PATH = "data/books"


def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)


def load_documents():
    files = list(Path(DATA_PATH).rglob("*.md"))
    documents = []
    for file_path in files:
        try:
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents.extend(loader.load())
        except UnicodeDecodeError:
            print(f"⚠️ 文件编码错误：{file_path}")
    return documents


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["。", "！", "？", "；", "\n", " ", ""],
        chunk_size=200,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )

    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    for i in range(len(chunks)):
        document = chunks[i]
        print(document.page_content)
        print(document.metadata)

    return chunks


def save_to_chroma(chunks: list[Document]):
    # 清理之前的数据库
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # 创建嵌入对象（Tongyi）
    embedding_function = TongyiEmbeddings(dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))

    # 存储向量数据库
    db = Chroma.from_documents(
        chunks,
        embedding_function,
        persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    generate_data_store()
