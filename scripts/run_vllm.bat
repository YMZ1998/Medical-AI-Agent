@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ===== 配置项（建议路径无空格、无中文） =====
set "MODEL_DIR=D:\huggingface_cache\models--Qwen--Qwen2.5-7B-Instruct\snapshots\a09a35458c702b33eeacc393d103063234e8bc28"
set "PORT=8000"

:: ===== 提示信息 =====
echo.
echo 正在启动 vLLM 容器...
echo 模型路径: %MODEL_DIR%
echo 使用镜像: vllm/vllm-openai:latest
echo 启动后访问: http://localhost:%PORT%
echo.

docker run --gpus all -it --rm -v "%MODEL_DIR%":/model -p %PORT%:8000 vllm/vllm-openai:latest /bin/bash

echo.
echo 容器内启动命令示例：
echo python3 -m vllm.entrypoints.openai.api_server --model /model --host 0.0.0.0 --port 8000
pause
