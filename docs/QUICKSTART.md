# 快速开始指南

本指南帮助您在5分钟内启动视频水印去除工具后端服务。

## 选择部署方式

根据您的需求选择合适的部署方式：

- **本地开发**: 适合开发和测试
- **Docker部署**: 适合快速部署和隔离环境
- **生产部署**: 适合生产环境，提供完整的监控和管理

---

## 方式一：本地开发（推荐用于开发）

### 前置要求

- Python 3.10+
- FFmpeg

### 步骤

```bash
# 1. 进入项目目录
cd backend

# 2. 启动服务（自动创建虚拟环境和安装依赖）
./run.sh
```

**就这么简单！** 服务将在 http://localhost:8000 启动。

访问 http://localhost:8000/docs 查看API文档。

---

## 方式二：Docker部署（推荐用于快速部署）

### 前置要求

- Docker
- Docker Compose

### 步骤

```bash
# 1. 进入项目目录
cd backend

# 2. 复制环境变量文件
cp .env.example .env

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

服务将在 http://localhost:8000 启动。

### 管理命令

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps
```

---

## 方式三：生产部署（推荐用于生产环境）

### 前置要求

- Python 3.10+
- FFmpeg
- Nginx（可选，用于反向代理）

### 步骤

```bash
# 1. 进入项目目录
cd backend

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置，设置 DEBUG=false

# 3. 启动生产服务
./start-production.sh
```

服务将在后台运行，使用 Gunicorn 作为生产服务器。

### 管理命令

```bash
# 停止服务
./stop-production.sh

# 查看日志
tail -f logs/error.log
tail -f logs/access.log
```

---

## 验证部署

无论使用哪种方式，都可以通过以下命令验证服务是否正常运行：

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应
{"status":"healthy"}
```

---

## 常用端点

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **上传视频**: POST http://localhost:8000/api/videos/upload
- **视频列表**: GET http://localhost:8000/api/videos

---

## 测试上传

使用curl测试视频上传：

```bash
curl -X POST "http://localhost:8000/api/videos/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/video.mp4"
```

---

## 下一步

- 查看 [API文档](http://localhost:8000/docs) 了解所有可用接口
- 阅读 [DEPLOYMENT.md](DEPLOYMENT.md) 了解详细部署配置
- 查看 [README.md](README.md) 了解项目功能和架构

---

## 故障排查

### 服务无法启动

```bash
# 检查Python版本
python3 --version  # 应该是 3.10+

# 检查FFmpeg
ffmpeg -version

# 查看错误日志
tail -f logs/error.log
```

### 端口被占用

```bash
# 查看端口占用
sudo lsof -i :8000

# 修改端口（编辑 .env 文件）
PORT=8001
```

### 权限问题

```bash
# 赋予脚本执行权限
chmod +x run.sh start-production.sh stop-production.sh
```

---

## 获取帮助

- **详细部署指南**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **API文档**: http://localhost:8000/docs
- **项目文档**: [README.md](README.md)

---

**祝您使用愉快！** 🎉
