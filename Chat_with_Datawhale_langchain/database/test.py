from langchain.vectorstores import Chroma
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.llms import OpenAI
from langchain.llms import HuggingFacePipeline
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from API import get_dashscope_api_key
from Chat_with_Datawhale_langchain.embedding.call_embedding import get_embedding

dashscope_api_key = get_dashscope_api_key()

import os

embedding = get_embedding("tongyi")

# embedding = OpenAIEmbeddings()
persist_directory = '../vector_db/chroma'
vectordb = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding
)
print(f"向量库中存储的数量：{vectordb._collection.count()}")
question = "llm_universe"
sim_docs = vectordb.similarity_search(question, k=10)
print(f"检索到的内容数：{len(sim_docs)}")
for i, sim_doc in enumerate(sim_docs):
    print(f"检索到的第{i}个内容: \n{sim_doc.page_content}", end="\n--------------\n")
