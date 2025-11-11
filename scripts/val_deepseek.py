from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    model_name = "deepseek-ai/deepseek-math-7b-base"

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        load_in_8bit=True,
        use_auth_token=True
    )
    model.eval()

    prompt = "介绍一下DeepSeek 7B模型的特点。"

    print(f"Encoding input: {prompt}")
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    print("Generating...")
    outputs = model.generate(**inputs, max_new_tokens=100)

    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\n=== 输出结果 ===")
    print(result)

if __name__ == "__main__":
    main()
