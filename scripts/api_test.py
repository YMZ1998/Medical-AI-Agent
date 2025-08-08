import requests
import time


def check_service(url, timeout=2, retries=5, interval=1):
    """
    检查指定 URL 的服务是否可用（支持重试）。

    Args:
        url (str): 服务地址
        timeout (int | float): 单次请求超时时间（秒）
        retries (int): 最大重试次数
        interval (int | float): 每次重试之间的等待时间（秒）

    Returns:
        tuple: (bool, dict | str)
               - bool: 服务是否可用
               - dict | str: 成功时返回响应 JSON，失败时返回错误信息
    """
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return True, r.json()
        except Exception as e:
            if attempt < retries:
                print(f"⚠️ 第 {attempt} 次尝试失败：{e}，{interval} 秒后重试...")
                time.sleep(interval)
            else:
                return False, str(e)


if __name__ == "__main__":
    ok, info = check_service(url="http://localhost:8000/v1/models", retries=10, interval=2)  # 例如最多重试 10 次，每次间隔 2 秒
    if ok:
        print("✅ 服务可用，返回：", info)
    else:
        print("❌ 服务尚未就绪：", info)
