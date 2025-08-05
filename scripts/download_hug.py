# from huggingface_hub import snapshot_download
#
# snapshot_download(repo_id="shibing624/ziya-llama-13b-medical-lora", local_dir="./models")

from transformers import AutoModelForCausalLM, AutoTokenizer
model_name = "Qwen/Qwen2.5-7B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=True, cache_dir="D:/huggingface_cache")
model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=True, cache_dir="D:/huggingface_cache")

