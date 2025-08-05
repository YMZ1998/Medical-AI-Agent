import torch
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM

# ✅ 模型路径（Chat 模型）
model_name = "Qwen/Qwen2.5-7B-Instruct"

# ✅ 加载模型和 tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",  # 自动选择 GPU
    torch_dtype=torch.float16,  # 使用半精度加速
    trust_remote_code=True
).eval()


# ✅ 聊天函数
def chat(user_input, history):
    # 构造聊天上下文
    messages = [{"role": "system", "content": "You are Qwen, a helpful assistant."}]
    for user, assistant in history[-2:]:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": user_input})

    # 使用 Qwen chat template
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # 编码输入并送入模型
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=True,
            temperature=0.7,
            top_p=0.8,
            repetition_penalty=1.05
        )

    # 解码新生成的 token 部分
    new_tokens = outputs[0][inputs.input_ids.shape[1]:]
    output_text = tokenizer.decode(new_tokens, skip_special_tokens=True)

    # 更新历史并返回
    history.append([user_input, output_text.strip()])
    return history, history, ""


# ✅ 构建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 Qwen Chatbot (Transformers + Gradio)")

    chatbot = gr.Chatbot(label="Qwen Chatbot").style(height=500)
    user_input = gr.Textbox(label="Your message", placeholder="Type your question here...", lines=1)
    state = gr.State([])

    send_btn = gr.Button("Send")
    send_btn.click(fn=chat, inputs=[user_input, state], outputs=[chatbot, state, user_input])
    user_input.submit(fn=chat, inputs=[user_input, state], outputs=[chatbot, state, user_input])

# ✅ 启动
demo.launch(server_port=7860)
