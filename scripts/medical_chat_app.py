import gradio as gr
import requests
import time

from scripts.medical_templates import medical_templates

# 📡 vLLM 服务地址（本地或局域网 IP）
url = "http://192.168.0.90:8000/v1/chat/completions"
headers = {"Content-Type": "application/json"}


# 🧠 动态构建 system prompt
def build_prompt(template_type, context, question):
    template = medical_templates.get(template_type, medical_templates["general"])
    return template.format(context=context.strip(), question=question.strip())


# 🌐 聊天主函数
messages = []  # 全局消息上下文


def medical_chat_fn(user_input, chat_history, template_type, context):
    # 构造 dynamic prompt，重置上下文
    system_prompt = build_prompt(template_type, context, user_input)
    messages.clear()
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_input})

    data = {
        "model": "doctor",
        "messages": messages[-2:],  # 当前系统提示 + 本轮提问
        "max_tokens": 512,
        "temperature": 0.7,
    }

    start_time = time.time()
    response = requests.post(url, json=data, headers=headers)
    elapsed = time.time() - start_time

    result = response.json()
    assistant_msg = result["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": assistant_msg})

    chat_history.append((user_input, f"{assistant_msg}  \n\n⏱️ 耗时：{elapsed:.2f} 秒"))
    return "", chat_history


# 🧹 清除函数
def clear_chat():
    messages.clear()
    return [], ""


# 🖼️ Gradio UI 构建
with gr.Blocks() as demo:
    gr.Markdown("# 🩺 医疗对话助手")
    gr.Markdown("通过选择不同提示词模板，获得专业的诊断、用药或综合医学建议。")

    with gr.Row():
        template_selector = gr.Dropdown(
            label="🧩 选择提示词模板",
            choices=["general", "diagnosis", "drug"],
            value="general"
        )
        context_box = gr.Textbox(
            label="📄 上下文（可选）",
            placeholder="例如：患者基本信息、已有诊断、实验室结果等",
            lines=4
        )

    chatbot = gr.Chatbot(label="👨‍⚕️ Assistant", show_copy_button=True, show_share_button=True, height=800)
    msg = gr.Textbox(label="💬 你的问题", placeholder="请输入医学相关问题，回车发送", lines=1)
    clear = gr.Button("🧹 清除对话")

    msg.submit(
        fn=medical_chat_fn,
        inputs=[msg, chatbot, template_selector, context_box],
        outputs=[msg, chatbot]
    )

    clear.click(fn=clear_chat, outputs=[chatbot, msg])

# 🚀 启动服务
demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
