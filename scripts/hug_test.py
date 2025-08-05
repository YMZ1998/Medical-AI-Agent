import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig


model = AutoModelForCausalLM.from_pretrained("shibing624/vicuna-baichuan-13b-chat", device_map='auto', torch_dtype=torch.float16, trust_remote_code=True)
model.generation_config = GenerationConfig.from_pretrained("shibing624/vicuna-baichuan-13b-chat", trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained("shibing624/vicuna-baichuan-13b-chat", trust_remote_code=True)
device = torch.device(0) if torch.cuda.is_available() else torch.device("cpu")

def generate_prompt(instruction):
    return f"""A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.USER: {instruction} ASSISTANT: """


sents = ['一岁宝宝发烧能吃啥药', "who are you?"]
for s in sents:
    q = generate_prompt(s)
    inputs = tokenizer(q, return_tensors="pt")
    inputs = inputs.to(device)

    generate_ids = model.generate(
        **inputs,
        max_new_tokens=512, 
    )

    output = tokenizer.batch_decode(generate_ids, skip_special_tokens=True)[0]
    print(output)
    print()