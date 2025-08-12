@echo off
chcp 65001 >nul

REM ===== 配置部分 =====
set REPOSITORY=vllm/vllm-openai
set TAG=latest
set VERSION=v1.0
set IMAGE_NAME=%REPOSITORY%:%TAG%
set SAVE_DIR=D:\docker_export

REM 把 / 替换成 -
set SAFE_REPOSITORY=%REPOSITORY:/=-%

echo %SAFE_REPOSITORY%
REM ====================

REM 确保保存目录存在
if not exist "%SAVE_DIR%" mkdir "%SAVE_DIR%"

REM 生成文件路径（版本号替代时间戳）
set FILE_NAME=%SAVE_DIR%\%SAFE_REPOSITORY%_%VERSION%.tar

echo.
echo 正在保存镜像 %IMAGE_NAME% 到 %FILE_NAME% ...
docker save -o "%FILE_NAME%" %IMAGE_NAME%

if %ERRORLEVEL% EQU 0 (
    echo 镜像已成功保存到 %FILE_NAME%
) else (
    echo 保存失败，请检查镜像名称是否正确
)

pause
