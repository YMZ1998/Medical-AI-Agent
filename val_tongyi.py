import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class QwenChatbot:
    def __init__(self, model_name="Qwen/Qwen3-8B"):
        print("加载 tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

        print("加载 model（建议使用 RTX 4090）...")
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",  # 自动使用 GPU
            torch_dtype=torch.float16,  # 使用 FP16 加速
            trust_remote_code=True
        ).eval()

        self.history = []

    def generate_response(self, user_input: str):
        # 构建上下文 + 当前用户输入
        self.history.append({"role": "user", "content": user_input})

        # 构造 chat prompt
        text = self.tokenizer.apply_chat_template(
            self.history,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize 输入并转到 GPU
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)

        # 使用推理模式生成响应
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,  # 限制响应长度，防卡死
                do_sample=True,  # 采样方式更自然
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1
            )

        # 解码输出内容（仅提取新增部分）
        generated_ids = outputs[0][inputs.input_ids.shape[1]:]
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        # 追加到历史记录
        self.history.append({"role": "assistant", "content": response})

        return response

    def reset(self):
        self.history = []


# Example: 连续对话模式
if __name__ == "__main__":
    chatbot = QwenChatbot()

    print("\n欢迎进入通义千问 Qwen3-8B 对话模式（输入 exit 退出）\n")

    while True:
        user_input = input("🧑 你：").strip() + ' /no_think'
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        response = chatbot.generate_response(user_input)
        print(f"🤖 千问：{response}\n")
