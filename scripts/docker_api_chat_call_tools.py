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
    "你是一个可以帮助用户聊天的智能助手。"
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
            return func_name, args
    except Exception:
        pass
    return None, None


from inspect import signature


def generate_tool_descriptions(tools: dict):
    descriptions = []
    for name, func in tools.items():
        doc = func.__doc__ or "无描述"
        try:
            sig = signature(func)
            params = ", ".join([p.name for p in sig.parameters.values()])
            example_args = ", ".join([f'{p.name}="..."' for p in sig.parameters.values()])
            example = f"{name}({example_args})"
        except Exception:
            params = "未知参数"
            example = name
        descriptions.append(
            f"工具名称: {name}\n"
            f"描述: {doc}\n"
            f"参数: {params}\n"
            f"示例: {example}\n"
        )
    return "\n".join(descriptions)


TOOL_DESCRIPTIONS = generate_tool_descriptions(TOOLS)


# ---------------- 主聊天函数 ----------------
def chat_with_model(user_input):
    print("--------------------------------------------------------------------------------")
    print("User:", user_input)
    # 给 LLM 提示可调用工具
    prompt = (
        f"以下是可用工具函数，用户可能会用到它们：\n"
        f"{TOOL_DESCRIPTIONS}\n"
        f"用户指令: {user_input}\n"
        f"如果需要调用工具函数，请严格输出 JSON 格式：{{'function': '...', 'args': {...}}}，"
        f"不要使用单引号，键和值必须用双引号,源文件路径为 src_path，目标文件路径为 dst_path。"
        f"否则只回答用户指令。"
    )
    # print("Prompt:", prompt)

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

    # 尝试解析函数调用
    func_name, args = parse_llm_output(assistant_msg)
    if func_name:
        print(f"[调用工具函数: {func_name}], {args}")
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
