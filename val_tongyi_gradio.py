import gradio as gr
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams


# ✅ 初始化 tokenizer 和模型（仅运行一次）
model_name = "Qwen/Qwen2.5-7B-Instruct-1M"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

llm = LLM(
    model=model_name,
    tensor_parallel_size=1,  # 你有几张显卡就设几张，如果是 4090 单卡就设为 1
    max_model_len=32768,
    enable_chunked_prefill=True,
    enforce_eager=True,
)

# ✅ 设置推理参数
sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.8,
    repetition_penalty=1.05,
    max_tokens=512
)


# ✅ 聊天函数（Gradio接口）
def chat(user_input, history):
    # 构造聊天上下文（Gradio历史格式是 [[user, assistant], ...]）
    messages = [{"role": "system", "content": "You are Qwen, a helpful assistant."}]
    for user, assistant in history:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": user_input})

    # 应用Qwen聊天模板
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # 模型推理
    outputs = llm.generate([prompt], sampling_params)
    output_text = outputs[0].outputs[0].text.strip()

    # 返回更新后的历史
    history.append([user_input, output_text])
    return history, history


# ✅ 构建 Gradio UI 界面
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 Qwen2.5 Chatbot with vLLM + Gradio")

    chatbot = gr.Chatbot(label="Qwen2.5 Chatbot").style(height=500)
    user_input = gr.Textbox(label="Your message", placeholder="Type your question here...", lines=1)
    state = gr.State([])

    send_btn = gr.Button("Send")

    send_btn.click(fn=chat, inputs=[user_input, state], outputs=[chatbot, state])
    user_input.submit(fn=chat, inputs=[user_input, state], outputs=[chatbot, state])

# ✅ 启动 Gradio 应用
demo.launch(server_name="0.0.0.0", server_port=7860)
