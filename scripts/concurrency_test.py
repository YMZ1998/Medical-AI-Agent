import requests
import concurrent.futures
import time

url = "http://localhost:8000/v1/chat/completions"
headers = {"Content-Type": "application/json"}


def send_request(index):
    data = {
        "model": "Qwen",
        "messages": [
            {"role": "system", "content": "你是医学助手"},
            {"role": "user", "content": f"这是第{index}个问题：高血压的诊断标准？"}
        ],
        "max_tokens": 512,
        "temperature": 0.7,
    }
    start = time.time()
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        elapsed = time.time() - start
        return f"线程 {index} 响应成功，耗时：{elapsed:.2f}s，内容片段：{response.json()['choices'][0]['message']['content'][:20]}"
    except Exception as e:
        return f"线程 {index} 失败：{str(e)}"

start_time = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(send_request, i) for i in range(20)]
    for future in concurrent.futures.as_completed(futures):
        print(future.result())
end_time = time.time()
print(f"总耗时: {end_time - start_time:.2f} 秒")
