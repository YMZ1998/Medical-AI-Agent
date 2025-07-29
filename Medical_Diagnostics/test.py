import os

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

from api_config import api_config

dashscope_api_key = api_config.get_api_key()

llm = ChatTongyi(
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen-turbo",
    temperature=0.3,
) | StrOutputParser()

chat_history = [
    SystemMessage(content="You are a helpful medical assistant named Bob.")
]

def chat(user_input: str):
    chat_history.append(HumanMessage(content=user_input))
    response = llm.invoke(chat_history)
    chat_history.append(AIMessage(content=response))
    return response

if __name__ == "__main__":
    while True:
        try:
            user_msg = input("🧑‍⚕️ You: ")
            if user_msg.lower() in ["exit", "quit"]:
                break
            bot_reply = chat(user_msg)
            print(f"🤖 Bob: {bot_reply}")
        except KeyboardInterrupt:
            break
