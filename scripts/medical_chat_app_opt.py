import gradio as gr
import requests
import time
from scripts.medical_templates import medical_templates

url = "http://192.168.0.90:8000/v1/chat/completions"
headers = {"Content-Type": "application/json"}


def build_prompt(template_type, user_context, question, chat_history):
    template = medical_templates.get(template_type, medical_templates["general"])
    history_str = ""
    for user_msg, bot_msg in chat_history[-3:]:
        history_str += f"用户：{user_msg}\n助手：{bot_msg}\n"
    full_context = (history_str + "\n" + user_context).strip()
    return template.format(context=full_context, question=question.strip())


def medical_chat_fn(user_input, chat_history, template_type, context, messages_state):
    if not user_input:
        return "", chat_history, "等待输入...", messages_state

    # 读取用户独立的上下文状态
    messages = messages_state or []

    system_prompt = build_prompt(template_type, context, user_input, chat_history)

    messages = []  # 清空历史（可改成保留历史）
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_input})

    data = {
        "model": "doctor",
        "messages": messages[-2:],  # 当前系统提示 + 用户提问
        "max_tokens": 512,
        "temperature": 0.7,
    }

    start_time = time.time()
    response = requests.post(url, json=data, headers=headers)
    elapsed = time.time() - start_time

    result = response.json()
    assistant_msg = result["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": assistant_msg})

    chat_history.append((user_input, assistant_msg))
    elapsed_str = f"{elapsed:.2f} 秒"

    return "", chat_history, elapsed_str, messages


def clear_chat():
    return [], "", "等待输入...", []


with gr.Blocks() as demo:
    gr.Markdown("# 🩺 医疗对话助手")
    gr.Markdown("请选择提示词模板，支持多轮历史和上下文输入。")

    with gr.Row():
        template_selector = gr.Dropdown(
            label="🧩 选择提示词模板",
            choices=["default", "general", "diagnosis", "drug"],
            value="default",
        )
        context_box = gr.Textbox(
            label="📄 上下文（可选）",
            placeholder="患者基本信息、已有诊断、实验室结果等",
            lines=4,
        )

    chatbot = gr.Chatbot(
        label="👨‍⚕️ Assistant",
        show_copy_button=True,
        show_share_button=True,
        height=800,
    )

    with gr.Row():
        with gr.Column(scale=20):
            msg = gr.Textbox(
                label="💬 你的问题",
                placeholder="请输入医学相关问题，回车发送",
                lines=1,
            )
        with gr.Column(scale=2):
            time_display = gr.Textbox(
                label="⏱️ 耗时",
                value="等待输入...",
                interactive=False,
                show_label=True,
                max_lines=1,
            )

    # 每个用户的消息上下文状态
    messages_state = gr.State([])

    clear = gr.Button("🧹 清除对话")

    msg.submit(
        fn=medical_chat_fn,
        inputs=[msg, chatbot, template_selector, context_box, messages_state],
        outputs=[msg, chatbot, time_display, messages_state],
    )

    clear.click(fn=clear_chat, outputs=[chatbot, msg, time_display, messages_state])

demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
