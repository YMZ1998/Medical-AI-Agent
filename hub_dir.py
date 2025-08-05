from huggingface_hub import hf_hub_download
import os

cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
print("Hugging Face 模型缓存目录:", cache_dir)
