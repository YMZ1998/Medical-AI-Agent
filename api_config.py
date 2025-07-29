import os
import dashscope
from dotenv import load_dotenv


class APIConfig:
    _instance = None

    def __new__(cls, env_path: str = "api.env"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(env_path)
        return cls._instance

    def _initialize(self, env_path: str):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(current_dir, env_path))

        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.app_id = os.getenv("DASHSCOPE_APP_ID")

        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is not set in the environment.")

        dashscope.api_key = self.api_key

        print("[✔] Dashscope API KEY 加载成功:", self.api_key[:6] + "..." + self.api_key[-4:])
        print("[✔] Dashscope APP ID 加载成功:", self.app_id[:6] + "..." + self.app_id[-4:])

    def get_api_key(self):
        print("api_key:", self.api_key[:6] + "..." + self.api_key[-4:])
        return self.api_key

    def get_app_id(self):
        print("app_id:", self.app_id[:6] + "..." + self.app_id[-4:])
        return self.app_id


api_config = APIConfig()

if __name__ == "__main__":
    api_key = api_config.get_api_key()
    app_id = api_config.get_app_id()
