import time
import requests
from fastapi import FastAPI, Query, Request
from pydantic import BaseModel
from typing import List, Tuple
from loguru import logger
import sys
from scripts.md_to_text import md_to_text
from scripts.medical_templates import medical_templates

MODEL_URL = "http://192.168.0.90:8000/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

app = FastAPI(title="Medical Chat API with Session History Limit")

# 会话历史存储，key=session_id，value=List[Tuple[user_msg, assistant_msg]]
session_store = {}

# 保留的最大对话轮数
MAX_HISTORY_ROUNDS = 5

# 配置 loguru，控制台和文件都打印，文件每日轮转，保留7天
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level}</level> | "
           "<level>{message}</level>",
    colorize=True,
)

logger.add(
    sink="logs/medical_chat_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # 每天凌晨0点分割日志文件
    retention="7 days",  # 保留最近7天日志
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    encoding="utf-8",
)


def build_prompt(template_type: str, user_context: str, question: str, chat_history: List[Tuple[str, str]],
                 medical_templates: dict):
    template = medical_templates.get(template_type, medical_templates["general"])
    history_str = ""
    for user_msg, bot_msg in chat_history[-MAX_HISTORY_ROUNDS:]:
        history_str += f"用户：{user_msg}\n助手：{bot_msg}\n"
    full_context = (history_str + "\n" + user_context).strip()
    return template.format(context=full_context, question=question.strip())


class ChatRequest(BaseModel):
    session_id: str
    question: str
    template_type: str = "default"
    context: str = ""


class ChatResponse(BaseModel):
    answer: str
    elapsed_seconds: float
    chat_history: List[Tuple[str, str]]


class ResetResponse(BaseModel):
    status: str
    message: str


@app.post("/chat", response_model=ChatResponse)
def medical_chat(req: ChatRequest, request: Request):
    logger.info(f"Received /chat request from session_id={req.session_id} question={req.question[:30]!r}...")
    if not req.question.strip():
        logger.warning("Empty question received, returning empty response.")
        return {"answer": "", "elapsed_seconds": 0, "chat_history": []}

    history = session_store.get(req.session_id, [])

    system_prompt = build_prompt(req.template_type, req.context, req.question, history, medical_templates)

    messages_state = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": req.question}
    ]

    start_time = time.time()
    try:
        response = requests.post(
            MODEL_URL,
            json={
                "model": "Qwen",
                "messages": messages_state,
                "max_tokens": 512,
                "temperature": 0.7,
            },
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error calling model API: {e}")
        return {"answer": "服务调用失败，请稍后重试。", "elapsed_seconds": 0, "chat_history": history}

    elapsed = time.time() - start_time
    result = response.json()
    assistant_msg = result["choices"][0]["message"]["content"]
    logger.info(f"Model API responded in {elapsed:.2f}s.")

    history.append((req.question, assistant_msg))
    session_store[req.session_id] = history[-MAX_HISTORY_ROUNDS:]

    return {
        "answer": (assistant_msg),
        "elapsed_seconds": round(elapsed, 2),
        "chat_history": session_store[req.session_id]
    }


@app.post("/reset", response_model=ResetResponse)
def reset_chat(session_id: str = Query(..., description="会话ID")):
    logger.info(f"Received /reset request for session_id={session_id}")
    session_store.pop(session_id, None)
    logger.info(f"Session {session_id} cleared.")
    return {"status": "ok", "message": f"Session {session_id} cleared"}


if __name__ == "__main__":
    import sys
    import uvicorn

    logger.info("Starting Medical Chat API server...")
    uvicorn.run(app, host="0.0.0.0", port=9000)
