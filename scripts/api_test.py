import requests

try:
    r = requests.get("http://localhost:8000/v1/models", timeout=2)
    print("✅ 服务可用，返回：", r.json())
except Exception as e:
    print("❌ 服务尚未就绪：", e)
