import re
from typing import Optional

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from Chat_with_Datawhale_langchain.qa_chain.get_vectordb import get_vectordb
from Chat_with_Datawhale_langchain.qa_chain.model_to_llm import model_to_llm
from Chat_with_Datawhale_langchain.utils.template import DEFAULT_TEMPLATE


class QAChainSelf:
    """
    不带历史记录的问答链
    """
    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        top_k: int = 4,
        file_path: Optional[str] = None,
        persist_path: Optional[str] = None,
        api_key: Optional[str] = None,
        embedding: str = "openai",
        embedding_key: Optional[str] = None,
        template: Optional[str] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.top_k = top_k
        self.file_path = file_path
        self.persist_path = persist_path
        self.api_key = api_key
        self.embedding = embedding
        self.embedding_key = embedding_key
        self.template = template or DEFAULT_TEMPLATE

        # 初始化向量数据库和大模型
        self.vectordb = get_vectordb(self.file_path, self.persist_path, self.embedding, self.embedding_key)

        self.llm = model_to_llm(self.model, self.temperature, self.api_key)

        self.qa_chain_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=self.template,
        )

        self.retriever = self.vectordb.as_retriever(
            search_type="similarity", search_kwargs={"k": self.top_k}
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.qa_chain_prompt},
        )

    def answer(
        self,
        question: str,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> str:
        """
        调用问答链，返回答案
        """
        if not question.strip():
            return "请输入有效问题"

        temperature = temperature if temperature is not None else self.temperature
        top_k = top_k if top_k is not None else self.top_k

        try:
            result = self.qa_chain({
                "query": question,
                "temperature": temperature,
                "top_k": top_k
            })
            answer = result.get("result", "未能生成答案")
            return re.sub(r"\\n", "<br/>", answer)
        except Exception as e:
            return f"出错了: {str(e)}"


if __name__ == '__main__':
    from api_config import api_config

    dashscope_api_key = api_config.get_api_key()
    chatbot = QAChainSelf(
        model="qwen-turbo",
        file_path="../../langchain_rag_tutorial/data/test.md",
        persist_path="./vector_db",
        api_key=dashscope_api_key,
        embedding="tongyi",
        embedding_key=dashscope_api_key
    )

    questions = ["这只猫名字叫什么？", "这只猫每天早上干什么？", "这是一个什么故事？"]
    for question in questions:
        answer = chatbot.answer(question)
        print("question:", question)
        print("answer:", answer)
