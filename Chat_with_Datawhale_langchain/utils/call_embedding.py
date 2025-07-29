import os

from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings

from Chat_with_Datawhale_langchain.utils.call_llm import parse_llm_api_key
from langchain_rag_tutorial.embeddings import TongyiEmbeddings


def get_embedding(embedding: str, embedding_key: str=None):
    if embedding == 'm3e':
        return HuggingFaceEmbeddings(model_name="moka-ai/m3e-base")
    if embedding_key == None:
        embedding_key = parse_llm_api_key(embedding)
    if embedding == "openai":
        return OpenAIEmbeddings(openai_api_key=embedding_key)
    elif embedding == "tongyi":
        return TongyiEmbeddings(dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))
    else:
        raise ValueError(f"embedding {embedding} not support ")
