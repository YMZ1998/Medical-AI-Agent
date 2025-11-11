from transformers import pipeline
import torch


model_id = r"D:\huggingface_cache\gpt-oss-20b"

pipe = pipeline(
    "text-generation",
    model=model_id,
    dtype=torch.int8,
    device_map="auto",
)

messages = [
    {"role": "user", "content": "Explain quantum mechanics clearly and concisely."},
]

outputs = pipe(
    messages,
    max_new_tokens=256,
)
print(outputs[0]["generated_text"][-1])
