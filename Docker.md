# Docker 常用命令速查表

## 1️⃣ 镜像操作

```bash
# 查看本地镜像
docker images

# 拉取镜像
docker pull <镜像名>:<标签>
docker pull ubuntu:22.04

# 删除镜像
docker rmi <镜像ID>
docker rmi 123abc

# 保存镜像到文件
docker save -o <文件名>.tar <镜像名>:<标签>
docker save -o ubuntu.tar ubuntu:22.04

# 从文件加载镜像
docker load -i <文件名>.tar
docker load -i ubuntu.tar

# 给镜像打新标签
docker tag <原镜像>:<标签> <新镜像>:<标签>
docker tag ubuntu:22.04 myubuntu:v1

# 搜索镜像
docker search <关键字>
docker search mysql
```

---

## 2️⃣ 容器操作

```bash
# 查看运行中的容器
docker ps

# 查看所有容器（含停止的）
docker ps -a

# 启动容器
docker start <容器ID>

# 停止容器
docker stop <容器ID>

# 重启容器
docker restart <容器ID>

# 删除容器
docker rm <容器ID>

# 运行容器（后台模式）
docker run -d --name <容器名> <镜像名>:<标签>
docker run -d --name myubuntu ubuntu:22.04

# 运行容器（交互模式）
docker run -it <镜像名>:<标签> /bin/bash
docker run -it ubuntu:22.04 /bin/bash

# 查看容器日志
docker logs <容器ID>
```

---

## 3️⃣ 数据卷（持久化）

```bash
# 创建数据卷
docker volume create <卷名>

# 查看数据卷
docker volume ls

# 删除数据卷
docker volume rm <卷名>

# 挂载数据卷到容器
docker run -v <卷名>:<容器路径> ...
docker run -v mydata:/data ubuntu
```

---

## 4️⃣ 网络管理

```bash
# 查看网络
docker network ls

# 创建网络
docker network create <网络名>

# 删除网络
docker network rm <网络名>

# 运行容器并指定网络
docker run --network <网络名> ...
```

---

## 5️⃣ 系统清理

```bash
# 删除所有停止的容器
docker container prune

# 删除所有未使用的镜像
docker image prune -a

# 删除所有未使用的卷
docker volume prune

# 删除所有未使用的网络
docker network prune

# 全面清理（谨慎操作）
docker system prune -a
```

---

## 6️⃣ 其他常用

```bash
# 查看 Docker 版本
docker --version

# 查看详细系统信息
docker info

# 进入运行中容器
docker exec -it <容器ID> /bin/bash

# 导出容器文件系统
docker export -o <文件名>.tar <容器ID>

# 从文件导入容器文件系统
docker import <文件名>.tar <新镜像名>
```

---