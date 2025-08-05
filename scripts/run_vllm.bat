@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ===== 配置项（建议路径无空格、无中文） =====
set "MODEL_DIR=D:\huggingface_cache\models--Qwen--Qwen2.5-7B-Instruct\snapshots\a09a35458c702b33eeacc393d103063234e8bc28"
set "PORT=8000"

echo.
echo 正在检查模型路径: %MODEL_DIR%
if not exist "%MODEL_DIR%" (
    echo ERROR: 模型路径不存在！请确认路径是否正确。
    pause
    exit /b 1
)

if not exist "%MODEL_DIR%\config.json" (
    echo ERROR: 模型目录下缺少 config.json 文件，可能不是有效模型路径。
    pause
    exit /b 1
)

echo 模型路径检查通过，继续启动容器...
echo.

echo.
echo 正在启动 vLLM 容器...
echo 模型路径: %MODEL_DIR%
echo 使用镜像: vllm/vllm-openai:latest
echo 启动后访问: http://localhost:%PORT%
echo.

docker run --gpus all -it --rm -v "%MODEL_DIR%":/model -p %PORT%:8000 --entrypoint python3 vllm/vllm-openai:latest -m vllm.entrypoints.openai.api_server --model /model --served-model-name doctor --host 0.0.0.0 --port 8000 --gpu-memory-utilization 0.8 --max-model-len 2048

echo.
echo 如果容器退出，服务也会停止。
pause
