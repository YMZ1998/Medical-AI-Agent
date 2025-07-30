from langchain.vectorstores import Chroma

from api_config import api_config

from Chat_with_Datawhale_langchain.utils.call_embedding import get_embedding

dashscope_api_key = api_config.get_api_key()

embedding = get_embedding("tongyi")

persist_directory = '../vector_db'
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
