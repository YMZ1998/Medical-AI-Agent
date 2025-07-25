import os

import dashscope
from dotenv import load_dotenv


def get_dashscope_api_key(env_path: str = "API.env") -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))

    load_dotenv(os.path.join(current_dir, env_path))

    api_key = os.getenv("DASHSCOPE_API_KEY")
    app_id = os.getenv("DASHSCOPE_APP_ID")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY is not set in the environment.")

    dashscope.api_key = api_key

    print("[✔] Dashscope API KEY 加载成功:", api_key[:6] + "..." + api_key[-4:])
    print("[✔] Dashscope APP ID 加载成功:", app_id[:6] + "..." + app_id[-4:])
    return api_key


if __name__ == "__main__":
    key = get_dashscope_api_key()
