import requests
import time
import json
import zipfile
import shutil
import os
import re

# -------------------- 配置 LLM --------------------
url = "http://localhost:8000/v1/chat/completions"
headers = {"Content-Type": "application/json"}

messages = [{"role": "system", "content": (
    "你是一个可以帮助用户聊天的智能助手。不要做任何假设。"
    "当用户指令涉及文件操作时，你可以调用工具函数，但只有必要时才调用。"
)}]


# ---------------- 工具函数注册 ----------------
def compress_file(src_path, dst_path):
    """压缩文件为 zip"""
    with zipfile.ZipFile(dst_path, "w") as zipf:
        zipf.write(src_path, os.path.basename(src_path))
    return f"Compressed {src_path} -> {dst_path}"


def move_file(src_path, dst_path):
    """移动文件"""
    shutil.move(src_path, dst_path)
    return f"Moved {src_path} -> {dst_path}"


TOOLS = {
    "compress_file": compress_file,
    "move_file": move_file,
}

# 参数映射（LLM输出的参数名 → 实际函数参数名）
PARAM_MAPPING = {
    "compress_file": {"src_path": "src_path", "dst_path": "dst_path", "source": "src_path", "source_path": "src_path",
                      "destination_path": "dst_path",
                      "dest": "dst_path"},
    "move_file": {"src_path": "src_path", "dst_path": "dst_path", "source": "src_path", "source_path": "src_path",
                  "dest": "dst_path", "destination_path": "dst_path"},
}


def map_args(func_name, args):
    if func_name in PARAM_MAPPING:
        mapping = PARAM_MAPPING[func_name]
        return {mapping.get(k, k): v for k, v in args.items()}
    return args


# ---------------- 清理 LLM 输出 ----------------
def clean_llm_json(output_text):
    cleaned = re.sub(r"```(?:json)?\n?|```", "", output_text).strip()
    return cleaned


# ---------------- 解析 LLM 输出 ----------------
def parse_llm_output(output_text):
    output_text = clean_llm_json(output_text)
    try:
        cmd = json.loads(output_text)
        func_name = cmd.get("function")
        args = cmd.get("args", {})
        if func_name in TOOLS:
            args = map_args(func_name, args)
            return func_name, args
    except Exception:
        pass
    return None, None


def detect_intent(user_input):
    """
    使用 LLM 判断用户意图
    返回: "file_op" 或 "chat"
    """
    prompt = (
        f"判断下面用户指令的意图，是文件操作(file_op)还是普通聊天(chat)。"
        f"严格返回 JSON 格式: {{\"intent\": \"file_op\"}} 或 {{\"intent\": \"chat\"}}\n"
        f"用户指令: {user_input}"
    )
    data = {
        "model": "Qwen",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 20,
        "temperature": 0
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    result = response.json()
    output_text = result["choices"][0]["message"]["content"]
    # 清理 JSON
    output_text = re.sub(r"```(?:json)?\n?|```", "", output_text).strip()
    try:
        intent_json = json.loads(output_text)
        return intent_json.get("intent", "chat")
    except Exception:
        return "chat"


# ---------------- 主聊天函数（改造版） ----------------
def chat_with_model(user_input):
    print("--------------------------------------------------------------------------------")
    print("User:", user_input)

    # 判断是否属于文件操作（意图识别）
    intent = detect_intent(user_input)
    is_file_op = intent == "file_op"

    if is_file_op:
        # 调用工具模式
        tool_descriptions = "\n".join([f"{k}: {TOOLS[k].__doc__}" for k in TOOLS])
        prompt = (
            f"以下是可用工具函数，用户可能会用到它们：\n"
            f"{tool_descriptions}\n"
            f"用户指令: {user_input}\n"
            f"请严格输出 JSON 格式：{{\"function\": \"...\", \"args\": {{...}}}}，"
            f"键和值必须用双引号,源文件路径为 src_path，目标文件路径为 dst_path。"
        )
    else:
        # 普通聊天模式
        prompt = (
            f"请简要地回答用户问题。\n"
            f"用户: {user_input}\n"
        )

    messages.append({"role": "user", "content": prompt})
    chat = messages[-2:]  # 最近上下文

    data = {
        "model": "Qwen",
        "messages": chat,
        "max_tokens": 512,
        "temperature": 0.7,
    }

    start_time = time.time()
    response = requests.post(url, json=data, headers=headers)
    elapsed = time.time() - start_time
    response.raise_for_status()
    result = response.json()
    assistant_msg = result["choices"][0]["message"]["content"]

    # 如果是文件操作意图，尝试解析工具调用
    if is_file_op:
        func_name, args = parse_llm_output(assistant_msg)
        if func_name:
            print(f"[调用工具函数: {func_name}], 参数: {args}")
            try:
                func_result = TOOLS[func_name](**args)
                assistant_msg += f"\n[工具执行结果]: {func_result}"
            except Exception as e:
                assistant_msg += f"\n[工具执行失败]: {str(e)}"

    messages.append({"role": "assistant", "content": assistant_msg})
    print(f"[耗时 {elapsed:.2f} 秒]")
    print("Assistant:", assistant_msg)
    print("--------------------------------------------------------------------------------")


# ---------------- CLI ----------------
if __name__ == "__main__":
    print("开始对话（输入 exit 退出）")

    # 测试单条指令
    test_inputs = ["你是谁，你会什么？",
                   "请把 D:\\debug\\output.txt 移动到 D:\\output.txt",
                   "请把 D:\\output.txt 压缩成 D:\\output.zip",
                   "请把 D:\\output.txt 移动到 D:\\debug\\output.txt",
                   "你刚刚做了什么？"
                   ]
    for test_input in test_inputs:
        chat_with_model(test_input)

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("结束对话。")
            break
        if user_input == "":
            continue
        chat_with_model(user_input)
