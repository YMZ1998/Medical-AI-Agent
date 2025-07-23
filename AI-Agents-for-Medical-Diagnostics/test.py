from langchain_community.chat_models import ChatTongyi
import os
from dotenv import load_dotenv

load_dotenv('API.env')

llm = ChatTongyi(
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen-turbo",
    temperature=0.3
)

response = llm.invoke("你是谁？")
print(response.content)
