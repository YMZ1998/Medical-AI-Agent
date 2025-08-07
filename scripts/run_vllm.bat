@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ===== 配置项（建议路径无空格、无中文） =====
set "MODEL_DIR=D:\huggingface_cache\models--Qwen--Qwen2.5-7B-Instruct\snapshots\a09a35458c702b33eeacc393d103063234e8bc28"
set "PORT=8000"
set "CONTAINER_NAME=dipper.agent"
set "GPU_COUNT=all"

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

:: 检查是否已有容器运行
echo.
echo 检查是否已有名为 %CONTAINER_NAME% 的容器在运行...
set CONTAINER_ID=
for /f %%i in ('docker ps -a -q -f "name=%CONTAINER_NAME%"') do set CONTAINER_ID=%%i

if defined CONTAINER_ID (
    echo 停止并删除旧容器 %CONTAINER_NAME% ...
    docker stop %CONTAINER_NAME%
    docker rm %CONTAINER_NAME%
) else (
    echo 没有名为 %CONTAINER_NAME% 的旧容器。
)


echo.
echo 启动 vLLM 容器（后台运行）...
echo 模型路径: %MODEL_DIR%
echo 容器名: %CONTAINER_NAME%
echo 端口映射: %PORT% -> 8000
echo 镜像: vllm/vllm-openai:latest
echo 访问地址: http://localhost:%PORT%
echo.

docker run -d --gpus all --name %CONTAINER_NAME% ^
  -v "%MODEL_DIR%":/model ^
  -p %PORT%:8000 ^
  --shm-size=1g --ulimit memlock=-1:-1 ^
  --entrypoint python3 vllm/vllm-openai:latest ^
  -m vllm.entrypoints.openai.api_server ^
  --model /model ^
  --served-model-name Qwen ^
  --host 0.0.0.0 ^
  --port 8000 ^
  --gpu-memory-utilization 0.8 ^
  --tensor-parallel-size 1 ^
  --max-model-len 4096 ^
  --max-num-seqs 32 ^
  --swap-space 20

if %errorlevel% neq 0 (
    echo 容器启动失败！
    pause
    exit /b 1
) else (
	echo Container started successfully, running in background.
	echo View logs: docker logs -f %CONTAINER_NAME%
	echo Stop container: docker stop %CONTAINER_NAME%
)

pause