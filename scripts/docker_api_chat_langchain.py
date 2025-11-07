import json
import os
import shutil
import zipfile

from langchain.agents import AgentType
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
from langchain_community.llms.vllm import VLLMOpenAI

# ================= 配置 vLLM =================
VLLM_BASE = "http://localhost:8000/v1"
MODEL_NAME = "Qwen"

llm = VLLMOpenAI(
    openai_api_base=VLLM_BASE,
    openai_api_key="EMPTY",
    model_name=MODEL_NAME,
    temperature=0.7,
    max_tokens=1024 * 3,
)

# ================= 工具函数 =================
def parse_args(arg):
    """解析 agent 参数"""
    src_path = dst_path = None
    if isinstance(arg, str):
        arg = arg.strip().strip('"').strip("'")
        if arg.startswith("{") and arg.endswith("}"):
            arg_dict = json.loads(arg)
            src_path = arg_dict.get("src_path")
            dst_path = arg_dict.get("dst_path")
        elif "src_path:" in arg and "dst_path:" in arg:
            for part in arg.split(","):
                if ":" in part:
                    k, v = part.split(":", 1)
                    if k.strip() == "src_path":
                        src_path = v.strip()
                    elif k.strip() == "dst_path":
                        dst_path = v.strip()
    elif isinstance(arg, (list, tuple)) and len(arg) == 2:
        src_path, dst_path = arg
    return src_path, dst_path

def move_file(*args, **kwargs) -> str:
    try:
        src_path, dst_path = None, None
        if args:
            src_path, dst_path = parse_args(args[0])
        if kwargs:
            src_path = kwargs.get("src_path", src_path)
            dst_path = kwargs.get("dst_path", dst_path)
        if not src_path or not dst_path:
            raise ValueError("必须提供 src_path 和 dst_path")
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.move(src_path, dst_path)
        return f"✅ 移动完成: {src_path} → {dst_path}"
    except Exception as e:
        return f"❌ 移动失败: {e}"

def compress_file(*args, **kwargs) -> str:
    try:
        src_path, dst_path = None, None
        if args:
            src_path, dst_path = parse_args(args[0])
        if kwargs:
            src_path = kwargs.get("src_path", src_path)
            dst_path = kwargs.get("dst_path", dst_path)
        if not src_path or not dst_path:
            raise ValueError("必须提供 src_path 和 dst_path")
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        with zipfile.ZipFile(dst_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.isdir(src_path):
                for root, dirs, files in os.walk(src_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zf.write(file_path, os.path.relpath(file_path, start=src_path))
            else:
                zf.write(src_path, os.path.basename(src_path))
        return f"✅ 压缩完成: {src_path} → {dst_path}"
    except Exception as e:
        return f"❌ 压缩失败: {e}"

# ================= 定义工具 =================
tools = [
    Tool(name="move_file", func=move_file, description="移动文件或文件夹，输入参数: src_path, dst_path"),
    Tool(name="compress_file", func=compress_file, description="压缩文件或文件夹为 zip，输入参数: src_path, dst_path")
]

# ================= 构建 Agent =================
system_message = SystemMessage(
    content="你是一个可以帮助用户聊天的智能助手。当用户指令涉及调用工具函数时，请执行相关操作，如果执行失败直接返回就行。否则直接回答问题即可。"
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    system_message=system_message,
    memory=memory
)

# ================= 统一处理 Agent 输出 =================
def get_agent_response(agent, user_input: str) -> str:
    try:
        response_dict = agent.invoke(user_input)
        if isinstance(response_dict, dict):
            return response_dict.get("output") or str(response_dict)
        return str(response_dict)
    except Exception as e:
        return f"❌ Agent 执行失败: {e}"

# ================= 测试与交互 =================
if __name__ == "__main__":
    test_inputs = [
        "你是谁，你会什么？",
        # "请把 D:\\debug\\output.txt 移动到 D:\\output.txt",
        "请把 D:\\output.txt 压缩成 D:\\output.zip",
        "请把 D:\\output.txt 移动到 D:\\debug\\output.txt",
        "你刚刚做了什么？"
    ]
    for user_input in test_inputs:
        print("User:", user_input)
        response = get_agent_response(agent, user_input)
        print("Assistant:", response)

    print("输入 exit 或 quit 退出")
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        response = get_agent_response(agent, user_input)
        print("Assistant:", response)
