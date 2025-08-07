# from huggingface_hub import snapshot_download
#
# snapshot_download(repo_id="shibing624/ziya-llama-13b-medical-lora", local_dir="./models")
import os

from huggingface_hub import snapshot_download

from transformers import AutoModelForCausalLM, AutoTokenizer

# model_name = "Qwen/Qwen2.5-7B-Instruct"
# model_name = "IDEA-CCNL/Ziya-LLaMA-13B-v1"
# model_name = "medalpaca/medalpaca-7b"
model_name = "Intelligent-Internet/II-Medical-8B-1706"
cache_dir = "D:/huggingface_cache"
local_dir=os.path.join(cache_dir, model_name.split("/")[-1])
os.makedirs(local_dir, exist_ok=True)
# tokenizer = AutoTokenizer.from_pretrained(model_name, token=True, cache_dir=cache_dir)
# model = AutoModelForCausalLM.from_pretrained(model_name, token=True, cache_dir=cache_dir)

snapshot_download(
    repo_id=model_name,  # 你要的模型名称
    local_dir=local_dir,  # 保存到本地的目录
    local_dir_use_symlinks=False  # 不使用软链接，方便后续复制
)
