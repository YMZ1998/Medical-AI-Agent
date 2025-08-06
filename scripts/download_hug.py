# from huggingface_hub import snapshot_download
#
# snapshot_download(repo_id="shibing624/ziya-llama-13b-medical-lora", local_dir="./models")

from transformers import AutoModelForCausalLM, AutoTokenizer

# model_name = "Qwen/Qwen2.5-7B-Instruct"
# model_name = "IDEA-CCNL/Ziya-LLaMA-13B-v1"
# model_name = "medalpaca/medalpaca-7b"
model_name = "Intelligent-Internet/II-Medical-8B-1706"

tokenizer = AutoTokenizer.from_pretrained(model_name, token=True, cache_dir="D:/huggingface_cache")
model = AutoModelForCausalLM.from_pretrained(model_name, token=True, cache_dir="D:/huggingface_cache")
