import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import os
from datetime import datetime
from http import HTTPStatus
from time import mktime
from urllib.parse import urlencode
from urllib.parse import urlparse
from wsgiref.handlers import format_date_time

import openai
from dashscope import Generation
from dotenv import load_dotenv, find_dotenv


def get_completion(prompt: str, model: str, temperature=0.1, api_key=None, max_tokens=2048):
    # 调用大模型获取回复，支持上述三种模型+gpt
    # arguments:
    # prompt: 输入提示
    # model：模型名
    # temperature: 温度系数
    # api_key：如名
    # max_tokens : 返回最长序列
    # return: 模型返回，字符串
    # 调用 GPT
    if model in ["gpt-3.5-turbo", "gpt-3.5-turbo-16k-0613", "gpt-3.5-turbo-0613", "gpt-4", "gpt-4-32k"]:
        return get_completion_gpt(prompt, model, temperature, api_key, max_tokens)
    elif model in ["qwen-turbo", "qwen-plus", "qwen-turbo-latest", "qwen-plus-latest"]:
        return get_completion_tongyi(prompt, model, temperature, api_key, max_tokens)
    else:
        return f"不正确的模型: {model}"


def get_completion_gpt(prompt: str, model: str, temperature: float, api_key: str, max_tokens: int):
    # 封装 OpenAI 原生接口
    if api_key == None:
        api_key = parse_llm_api_key("openai")
    openai.api_key = api_key
    # 具体调用
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,  # 模型输出的温度系数，控制输出的随机程度
        max_tokens=max_tokens,  # 回复最大长度
    )
    # 调用 OpenAI 的 ChatCompletion 接口
    return response.choices[0].message["content"]


def get_completion_tongyi(prompt: str,
                          model: str = "qwen-turbo",
                          temperature: float = 0.7,
                          api_key: str = None,
                          max_tokens: int = 1024) -> str:
    """
    使用 DashScope 通义千问模型生成回复。

    参数:
        prompt (str): 输入提示词
        model (str): 通义模型名，例如 "qwen-turbo"
        temperature (float): 随机性
        api_key (str): DashScope API 密钥
        max_tokens (int): 最大输出 token 数量

    返回:
        str: 模型回复文本
    """
    if api_key is None:
        api_key = parse_llm_api_key("tongyi")

    Generation.api_key = api_key

    try:
        response = Generation.call(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="message"  # 返回格式：message 或 text
        )
    except Exception as e:
        raise RuntimeError(f"DashScope 调用失败: {e}")

    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"DashScope 错误 {response.status_code}: {response.message}")

    return response.output.choices[0].message.content


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws, one, two):
    print(" ")


# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question, temperature=ws.temperature,
                                 max_tokens=ws.max_tokens))
    ws.send(data)


# 收到websocket消息的处理
def on_message(ws, message):
    # print(message)
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        print(content, end="")
        global answer
        answer += content
        # print(1)
        if status == 2:
            ws.close()


def gen_params(appid, domain, question, temperature, max_tokens):
    """
    通过appid和用户的提问来生成请参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "random_threshold": 0.5,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


def parse_llm_api_key(model: str, env_file: dict() = None):
    """
    通过 model 和 env_file 的来解析平台参数
    """
    if env_file == None:
        _ = load_dotenv(find_dotenv())
        env_file = os.environ
    if model == "openai":
        return env_file["OPENAI_API_KEY"]
    elif model == "tongyi":
        return env_file["DASHSCOPE_API_KEY"]
    else:
        raise ValueError(f"model{model} not support!!!")
