import os
from dotenv import load_dotenv
import dashscope


def get_dashscope_api_key(env_path: str = "API.env") -> str:
    load_dotenv(env_path)

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY is not set in the environment.")

    dashscope.api_key = api_key

    print("[✔] Dashscope API KEY 加载成功:", api_key[:6] + "..." + api_key[-4:])
    return api_key

if __name__ == "__main__":
    key = get_dashscope_api_key()