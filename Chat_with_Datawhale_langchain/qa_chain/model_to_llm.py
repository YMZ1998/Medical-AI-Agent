from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatTongyi

from Chat_with_Datawhale_langchain.llm.call_llm import parse_llm_api_key


def model_to_llm(model: str = None,
                 temperature: float = 0.0,
                 api_key: str = None):
    """
    OpenAI：model,temperature,api_key
    通义千问：model,temperature,api_key
    """

    if model in ["gpt-3.5-turbo", "gpt-3.5-turbo-16k-0613", "gpt-3.5-turbo-0613", "gpt-4", "gpt-4-32k"]:
        if api_key is None:
            api_key = parse_llm_api_key("openai")
        llm = ChatOpenAI(model_name=model, temperature=temperature, openai_api_key=api_key)

    elif model in [
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-max-longcontext",
    ]:
        if api_key is None:
            api_key = parse_llm_api_key("tongyi")
        llm = ChatTongyi(dashscope_api_key=api_key, model_name=model, temperature=temperature)

    else:
        raise ValueError(f"model {model} not supported!!!")

    return llm
