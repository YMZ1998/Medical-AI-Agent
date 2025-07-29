from API import api_config


class APPConfig:
    def __init__(self):
        # API Key
        self.dashscope_api_key = api_config.get_api_key()

        # 模型配置
        self.llm_model_dict = {
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"],
            "tongyi": ["qwen-turbo", "qwen-plus", "qwen-turbo-latest", "qwen-plus-latest"]
        }
        self.llm_model_list = sum(self.llm_model_dict.values(), [])
        self.init_llm = "qwen-turbo"

        # 嵌入模型配置
        self.embedding_model_list = ["tongyi", "openai"]
        self.init_embedding_model = "tongyi"

        # 向量库路径
        self.default_db_path = "./knowledge_db"
        self.default_persist_path = "./vector_db"

        # UI 相关资源路径
        self.aigc_avatar_path = "./figures/aigc_avatar.png"
        self.datawhale_avatar_path = "./figures/datawhale_avatar.png"
        self.aigc_logo_path = "./figures/aigc_logo.png"
        self.datawhale_logo_path = "./figures/datawhale_logo.png"


if __name__ == "__main__":
    config = APPConfig()
    print(config.llm_model_dict)
