from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from Chat_with_Datawhale_langchain.app_config import app_config
from Chat_with_Datawhale_langchain.qa_chain.chat_qa_chain_simple import Chat_QA_chain_simple
from Chat_with_Datawhale_langchain.utils.template import medical_templates
from qa_chain.QA_chain_self import QAChainSelf


class QARequest(BaseModel):
    question: str
    init_llm: str = app_config.init_llm
    default_db_path: str = app_config.default_db_path
    default_persist_path: str = app_config.default_persist_path
    dashscope_api_key: str = app_config.dashscope_api_key
    init_embedding_model: str = app_config.init_embedding_model


# 默认 prompt 模板
mode = "general"  # 可选 "general", "vulnerable", "diagnosis"
print(medical_templates.get(mode))
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
    # chain = QAChainSelf(
    #     model=item.init_llm,
    #     file_path=item.default_db_path,
    #     persist_path=item.default_persist_path,
    #     api_key=item.dashscope_api_key,
    #     embedding=item.init_embedding_model,
    #     template=medical_templates.get(mode),
    #     embedding_key=item.dashscope_api_key
    # )
    chain = Chat_QA_chain_simple(
        model=item.init_llm,
        use_history=False,
        api_key=item.dashscope_api_key,
        template=medical_templates.get(mode)
    )
    response = chain.answer(question=item.question)
    return {"response": response}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
