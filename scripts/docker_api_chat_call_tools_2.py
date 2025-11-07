import requests
import time
import json
import zipfile
import shutil
import os
import re
from inspect import signature

# -------------------- 配置 LLM --------------------
VLLM_URL = "http://localhost:8000/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

# 各类 LLM 对应的消息缓存
MEMORY = {
    "chat": [],
    "file_ops": [],
    "tech": []
}

# ---------------- 工具函数 ----------------
def compress_file(src_path, dst_path):
    """压缩文件或目录为 zip"""
    try:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        with zipfile.ZipFile(dst_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.isdir(src_path):
                for root, dirs, files in os.walk(src_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zf.write(file_path, os.path.relpath(file_path, start=src_path))
            else:
                zf.write(src_path, os.path.basename(src_path))
        return f"✅ 压缩完成: {src_path} -> {dst_path}"
    except Exception as e:
        return f"❌ 压缩失败: {e}"

def move_file(src_path, dst_path):
    """移动文件或文件夹"""
    try:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.move(src_path, dst_path)
        return f"✅ 移动完成: {src_path} -> {dst_path}"
    except Exception as e:
        return f"❌ 移动失败: {e}"

TOOLS = {
    "compress_file": compress_file,
    "move_file": move_file
}

# 参数映射
PARAM_MAPPING = {
    "compress_file": {"src_path": "src_path", "dst_path": "dst_path", "source": "src_path",
                      "source_path": "src_path", "destination_path": "dst_path", "dest": "dst_path"},
    "move_file": {"src_path": "src_path", "dst_path": "dst_path", "source": "src_path",
                  "source_path": "src_path", "dest": "dst_path", "destination_path": "dst_path"}
}

def map_args(func_name, args):
    if func_name in PARAM_MAPPING:
        mapping = PARAM_MAPPING[func_name]
        return {mapping.get(k, k): v for k, v in args.items()}
    return args

# ---------------- 生成详细工具描述 ----------------
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

# ---------------- LLM 输出解析 ----------------
def clean_llm_json(output_text):
    return re.sub(r"```(?:json)?\n?|```", "", output_text).strip()

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

# ---------------- 聊天/工具调用 ----------------
def chat_with_model(user_input, llm_type="chat"):
    print("--------------------------------------------------------------------------------")
    print("User:", user_input)

    memory = MEMORY[llm_type]

    # 构造 prompt
    prompt = (
        f"以下是可用工具函数及详细信息：\n{TOOL_DESCRIPTIONS}\n"
        f"用户指令: {user_input}\n"
        f"如果需要调用工具函数，请严格输出 JSON 格式：{{\"function\": \"...\", \"args\": {{...}}}}, "
        f"键和值必须用双引号，否则只回答用户指令。"
    )

    memory.append({"role": "user", "content": prompt})
    chat = memory[-6:]  # 最近上下文

    data = {
        "model": "Qwen",
        "messages": chat,
        "max_tokens": 512,
        "temperature": 0.7,
    }

    start_time = time.time()
    response = requests.post(VLLM_URL, json=data, headers=HEADERS)
    elapsed = time.time() - start_time
    response.raise_for_status()
    result = response.json()
    assistant_msg = result["choices"][0]["message"]["content"]

    # 尝试解析函数调用
    func_name, args = parse_llm_output(assistant_msg)
    if func_name:
        print(f"[调用工具函数: {func_name}], 参数: {args}")
        try:
            func_result = TOOLS[func_name](**args)
            assistant_msg += f"\n[工具执行结果]: {func_result}"
        except Exception as e:
            assistant_msg += f"\n[工具执行失败]: {str(e)}"

    memory.append({"role": "assistant", "content": assistant_msg})
    print(f"[耗时 {elapsed:.2f} 秒]")
    print("Assistant:", assistant_msg)
    print("--------------------------------------------------------------------------------")

# ---------------- CLI ----------------
if __name__ == "__main__":
    print("开始对话（输入 exit 或 quit 退出）")

    test_inputs = [
        "你是谁，你会什么？",
        "请把 D:\\debug\\output.txt 移动到 D:\\output.txt",
        "请把 D:\\output.txt 压缩成 D:\\output.zip",
        "请把 D:\\output.txt 移动到 D:\\debug\\output.txt",
        "你刚刚做了什么？"
    ]
    for inp in test_inputs:
        llm_type = "file_ops" if re.search(r"(移动|压缩|文件|zip)", inp) else "chat"
        chat_with_model(inp, llm_type)

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("结束对话。")
            break
        if user_input == "":
            continue
        llm_type = "file_ops" if re.search(r"(移动|压缩|文件|zip)", user_input) else "chat"
        chat_with_model(user_input, llm_type)
