from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatTongyi

from Chat_with_Datawhale_langchain.utils.call_llm import parse_llm_api_key
from Chat_with_Datawhale_langchain.app_config import app_config

# 注册模型构造器
LLM_BUILDERS = {
    "openai": lambda model, temp, key: ChatOpenAI(model_name=model, temperature=temp, openai_api_key=key),
    "tongyi": lambda model, temp, key: ChatTongyi(model_name=model, temperature=temp, dashscope_api_key=key),
}


def model_to_llm(model: str = None,
                 temperature: float = 0.0,
                 api_key: str = None):
    """
    根据模型名称返回对应的 LLM 实例
    支持 openai / 通义千问 等
    """

    for platform, model_list in app_config.llm_model_dict.items():
        if model in model_list:
            if api_key is None:
                api_key = parse_llm_api_key(platform)
            if platform in LLM_BUILDERS:
                return LLM_BUILDERS[platform](model, temperature, api_key)
            else:
                raise ValueError(f"未注册的平台: {platform}")

    raise ValueError(f"不支持的模型: {model}")


if __name__ == "__main__":
    llm = model_to_llm("qwen-turbo", 2, "qqq")
    print("模型名:", getattr(llm, 'model_name', 'N/A'))
