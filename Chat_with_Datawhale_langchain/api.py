from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from Chat_with_Datawhale_langchain.app_config import app_config
from qa_chain.QA_chain_self import QAChainSelf


class QARequest(BaseModel):
    question: str
    init_llm: str = app_config.init_llm
    default_db_path: str = app_config.default_db_path
    default_persist_path: str = app_config.default_persist_path
    dashscope_api_key: str = app_config.dashscope_api_key


# 默认 prompt 模板
DEFAULT_TEMPLATE = """
你是一个专业医生，请根据提供的上下文简明准确地回答用户问题。

- 语言简洁清晰，逻辑通顺。

上下文：
{context}

问题：
{question}

回答：
"""
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def get_response(item: QARequest):
    chain = QAChainSelf(
        model=item.init_llm,
        file_path=item.default_db_path,
        persist_path=item.default_persist_path,
        api_key=item.dashscope_api_key,
        embedding="tongyi",  # 或也可以从 item 中传入
        template=DEFAULT_TEMPLATE,
        embedding_key=item.dashscope_api_key
    )
    response = chain.answer(question=item.question)
    return {"response": response}


# 可选：本地调试运行
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
