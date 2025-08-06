import aiohttp
import asyncio
import time

API_URL = "http://localhost:8000/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

payload = {
    "model": "doctor",
    "messages": [{"role": "user", "content": "你好，请问感冒怎么办？"}],
    "temperature": 0.7
}

async def fetch(session, idx):
    start = time.time()
    try:
        async with session.post(API_URL, headers=HEADERS, json=payload, timeout=10) as resp:
            resp.raise_for_status()
            result = await resp.json()
            duration = time.time() - start
            print(f"[{idx}] 耗时: {duration:.3f} 秒，回复: {result['choices'][0]['message']['content'][:20]}")
    except aiohttp.ClientResponseError as e:
        duration = time.time() - start
        print(f"[{idx}] HTTP错误: 状态码 {e.status}，耗时: {duration:.3f} 秒")
    except asyncio.TimeoutError:
        duration = time.time() - start
        print(f"[{idx}] 请求超时，耗时: {duration:.3f} 秒")
    except aiohttp.ClientConnectionError:
        duration = time.time() - start
        print(f"[{idx}] 连接错误，耗时: {duration:.3f} 秒")
    except Exception as e:
        duration = time.time() - start
        print(f"[{idx}] 其他异常: {e}，耗时: {duration:.3f} 秒")

async def main():
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, i) for i in range(20)]
        await asyncio.gather(*tasks)
    end_time = time.time()
    print(f"总耗时: {end_time - start_time:.2f} 秒")

if __name__ == "__main__":
    asyncio.run(main())
