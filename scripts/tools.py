import inspect
import json
import os
import re
import shutil
import zipfile

# ---------------- 工具注册系统 ----------------
TOOLS = {}


def tool(name, desc):
    """注册工具函数到全局 TOOLS 字典"""

    def wrapper(func):
        sig = inspect.signature(func)
        TOOLS[name] = {
            "func": func,
            "desc": desc,
            "params": list(sig.parameters.keys())
        }
        return func

    return wrapper


# ---------------- 工具函数定义 ----------------
@tool("compress_file", "压缩文件为 zip")
def compress_file(src_path, dst_path):
    """压缩文件为 zip"""
    with zipfile.ZipFile(dst_path, "w") as zipf:
        zipf.write(src_path, os.path.basename(src_path))
    return f"已压缩 {src_path} → {dst_path}"


@tool("move_file", "移动文件，从src_path到dst_path")
def move_file(src_path, dst_path):
    """移动文件"""
    if not os.path.exists(src_path):
        return f"❌ 文件不存在: {src_path}"
    shutil.move(src_path, dst_path)
    return f"已移动 {src_path} → {dst_path}"


@tool("read_file", "读取文件并打印前几行内容")
def read_file(file_path, max_lines=10):
    """读取文本文件内容并打印前 max_lines 行"""
    if not os.path.exists(file_path):
        return f"❌ 文件不存在: {file_path}"
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            preview = "".join(lines[:max_lines])
            return f"文件 {file_path} 前 {max_lines} 行内容:\n{preview}"
    except Exception as e:
        return f"读取失败: {str(e)}"


# ---------------- 工具执行接口 ----------------
def execute_tool(tool_name, **kwargs):
    """统一执行接口"""
    if tool_name not in TOOLS:
        raise ValueError(f"未知工具: {tool_name}")
    func = TOOLS[tool_name]["func"]
    return func(**kwargs)


def generate_tool_descriptions(tools: dict):
    """
    生成工具描述字符串。
    假设 tools 的 value 格式为: {"func": <callable>, "desc": str, "params": [...]}
    """
    descriptions = []
    for name, meta in tools.items():
        # meta 可能是直接的函数（兼容旧格式）或字典（当前格式）
        if isinstance(meta, dict):
            func = meta.get("func")
            desc = meta.get("desc") or (func.__doc__ if func else "无描述")
            params_list = meta.get("params")
            # 如果没有显式 params，尝试从函数签名获取
            if not params_list and callable(func):
                try:
                    sig = inspect.signature(func)
                    params_list = [p.name for p in sig.parameters.values()]
                except Exception:
                    params_list = []
        elif callable(meta):
            func = meta
            desc = func.__doc__ or "无描述"
            try:
                sig = inspect.signature(func)
                params_list = [p.name for p in sig.parameters.values()]
            except Exception:
                params_list = []
        else:
            continue

        params = ", ".join(params_list) if params_list else "无"
        example_args = ", ".join([f'{p}="..."' for p in params_list]) if params_list else ""
        example = f"{name}({example_args})" if example_args else f"{name}()"

        descriptions.append(
            f"工具名称: {name}\n"
            f"描述: {desc}\n"
            f"参数: {params}\n"
            f"示例: {example}\n"
        )
    return "\n".join(descriptions)


TOOL_DESCRIPTIONS = generate_tool_descriptions(TOOLS)


# ---------------- 清理 LLM 输出 ----------------
def clean_llm_json(output_text):
    cleaned = re.sub(r"```(?:json)?\n?|```", "", output_text).strip()
    return cleaned


# ---------------- 解析 LLM 输出 ----------------
def parse_llm_output(output_text):
    print("[LLM 输出]:", output_text)
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


# ---------------- 测试 ----------------
if __name__ == "__main__":
    print("工具描述：\n", TOOL_DESCRIPTIONS)

    # 示例：
    output_texts = [
        json.dumps(
            {"function": "move_file",
             "args": {"src_path": "D:\\output.txt", "dst_path": "D:\\debug\\output.txt"}}),
        json.dumps({
            "function": "move_file",
            "args": {"src_path": "D:\\debug\\output.txt", "dst_path": "D:\\output.txt"}})]

    for output_text in output_texts:
        func_name, args = parse_llm_output(output_text)
        print(f"工具名称: {func_name}, 参数: {args}")
        result = execute_tool("move_file", **args)
        print(result)
