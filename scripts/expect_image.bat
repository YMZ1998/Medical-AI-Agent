@echo off
chcp 65001 >nul

REM ===== 配置部分 =====
set REPOSITORY=vllm/vllm-openai
set TAG=latest
set IMAGE_NAME=%REPOSITORY%:%TAG%
set SAVE_DIR=D:\docker_export

REM 把 / 替换成 -
set SAFE_REPOSITORY=%REPOSITORY:/=-%

echo %SAFE_REPOSITORY%
REM ====================

for /f "tokens=2 delims==" %%i in ('wmic os get LocalDateTime /value ^| find "="') do set ldt=%%i
REM ldt格式: 20250811171605.123456+480
set yyyy=%ldt:~0,4%
set mm=%ldt:~4,2%
set dd=%ldt:~6,2%
set hh=%ldt:~8,2%
set min=%ldt:~10,2%
set ss=%ldt:~12,2%

set TIMESTAMP=%yyyy%%mm%%dd%_%hh%%min%%ss%

REM 确保保存目录存在
if not exist "%SAVE_DIR%" mkdir "%SAVE_DIR%"

REM 生成文件路径
set FILE_NAME=%SAVE_DIR%\%SAFE_REPOSITORY%_%TIMESTAMP%.tar

echo.
echo 正在保存镜像 %IMAGE_NAME% 到 %FILE_NAME% ...
docker save -o "%FILE_NAME%" %IMAGE_NAME%

if %ERRORLEVEL% EQU 0 (
    echo 镜像已成功保存到 %FILE_NAME%
) else (
    echo 保存失败，请检查镜像名称是否正确
)
