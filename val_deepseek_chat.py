from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def main():
    model_path = r"C:\Users\Admin\.cache\huggingface\hub\models--deepseek-ai--deepseek-math-7b-base\snapshots\036a8c6189aac6e2fc4e07b46e1e57c6b647bca5"  # 替换为你本地路径

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",  # 自动分配到 4090
        torch_dtype=torch.float16  # 用 FP16 提高速度
    ).eval()

    print("模型设备：", model.device)

    while True:
        prompt = input("\nUser: ").strip()
        if prompt.lower() in ["exit", "quit", "q"]:
            break

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.inference_mode():  # 开启推理模式加速
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("\nAssistant:", result)


if __name__ == "__main__":
    main()
