@echo off
chcp 65001 >nul

set IMAGE_FILE=D:\docker_export\ubuntu_20250811_172138.tar
set NEW_IMAGE_NAME=datu
set NEW_IMAGE_TAG=v1.0
set NEW_IMAGE=%NEW_IMAGE_NAME%:%NEW_IMAGE_TAG%
set ORIGINAL_IMAGE=ubuntu:latest

REM 先检查新镜像是否存在
docker image inspect %NEW_IMAGE% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 新镜像 %NEW_IMAGE% 已存在，正在删除 ...
    docker rmi -f %NEW_IMAGE%
)

echo 正在加载镜像文件：%IMAGE_FILE%
docker load -i "%IMAGE_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo 镜像加载失败！
    pause
    exit /b 1
)

echo 给镜像重新命名为 %NEW_IMAGE%
docker tag %ORIGINAL_IMAGE% %NEW_IMAGE%

echo 删除旧镜像标签 %ORIGINAL_IMAGE%
docker rmi %ORIGINAL_IMAGE%

docker image ls

echo 操作完成！
pause
