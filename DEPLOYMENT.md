# 部署指南 / Deployment Guide

视频水印去除工具的完整部署指南，包括前后端的本地开发、Docker部署和生产环境部署。

> **提示**: 如果您想快速开始，请查看 [快速开始指南](./docs/QUICKSTART.md)

## 📋 目录 / Table of Contents

- [系统要求](#系统要求)
- [快速部署（Docker Compose）](#快速部署docker-compose)
- [本地开发部署](#本地开发部署)
- [生产环境部署](#生产环境部署)
- [环境变量配置](#环境变量配置)
- [性能优化](#性能优化)
- [监控和维护](#监控和维护)
- [故障排查](#故障排查)

## 📚 相关文档 / Related Documentation

- **[快速开始](./docs/QUICKSTART.md)** - 5分钟快速部署
- **[API文档](./API_DOCUMENTATION.md)** - API接口文档
- **[常见问题](./FAQ.md)** - 问题排查指南
- **[后端说明](./docs/BACKEND_README.md)** - 后端详细文档
- **[前端说明](./docs/FRONTEND_README.md)** - 前端详细文档

## 🖥 系统要求 / System Requirements

### 硬件要求 / Hardware

- **CPU**: 4核心或以上（推荐8核心）
- **内存**: 8GB或以上（推荐16GB）
- **存储**: 100GB或以上可用空间
- **网络**: 稳定的网络连接

### 软件要求 / Software

#### Docker部署（推荐）
- Docker 20.10+
- Docker Compose 1.29+

#### 本地开发
- Python 3.10+
- Node.js 18+
- FFmpeg 4.0+
- Nginx（生产环境）

## 🚀 快速部署（Docker Compose）

这是最简单的部署方式，适合快速体验和生产环境使用。

### 1. 克隆项目

```bash
git clone <repository-url>
cd video-watermark-remover
```

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 根据需要编辑 .env 文件
```

### 3. 启动服务

```bash
# 构建并启动所有服务（后端 + 前端）
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问应用

- **前端界面**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 5. 停止服务

```bash
docker-compose down
```

### 6. 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

## 💻 本地开发部署 / Local Development

### 后端部署

#### 1. 安装系统依赖

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3-pip ffmpeg
```

**macOS**:
```bash
brew install python@3.10 ffmpeg
```

**Windows**:
- 下载并安装 [Python 3.10+](https://www.python.org/downloads/)
- 下载并安装 [FFmpeg](https://ffmpeg.org/download.html)

#### 2. 配置后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
```

#### 3. 启动后端服务

```bash
# 使用启动脚本（推荐）
chmod +x run.sh
./run.sh

# 或直接使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 启动。

### 前端部署

#### 1. 安装依赖

```bash
cd frontend

# 安装Node.js依赖
npm install
```

#### 2. 启动开发服务器

```bash
npm run dev
```

前端服务将在 http://localhost:3000 启动。

#### 3. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

## 🏭 生产环境部署 / Production Deployment

### 方案一：Docker Compose 部署（推荐）

这是最简单且推荐的生产部署方式。

#### 1. 准备服务器

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo apt-get install docker-compose-plugin
```

#### 2. 配置应用

```bash
# 克隆项目
git clone <repository-url>
cd video-watermark-remover/backend

# 配置生产环境变量
cp .env.example .env.production
nano .env.production
```

**重要配置**:
```bash
DEBUG=false
HOST=0.0.0.0
PORT=8000
MAX_FILE_SIZE=5368709120
```

#### 3. 启动服务

```bash
# 使用生产配置启动
docker-compose --env-file .env.production up -d

# 查看日志
docker-compose logs -f
```

#### 4. 配置域名和SSL

如果需要使用域名和HTTPS，可以在前面添加Nginx反向代理：

创建 `/etc/nginx/sites-available/videoapp`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # 代理到前端容器
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/videoapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 获取SSL证书
sudo certbot --nginx -d yourdomain.com
```

### 方案二：分离部署

如果需要更灵活的部署方式，可以分别部署前后端。

#### 后端部署

1. **创建应用用户**

```bash
sudo useradd -m -s /bin/bash videoapp
sudo su - videoapp
```

2. **部署应用**

```bash
git clone <repository-url>
cd video-watermark-remover/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 配置环境变量
cp .env.example .env
nano .env
```

3. **配置Systemd服务**

创建 `/etc/systemd/system/videoapp-backend.service`:

```ini
[Unit]
Description=Video Watermark Removal Backend
After=network.target

[Service]
Type=simple
User=videoapp
WorkingDirectory=/home/videoapp/video-watermark-remover/backend
Environment="PATH=/home/videoapp/video-watermark-remover/backend/venv/bin"
ExecStart=/home/videoapp/video-watermark-remover/backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable videoapp-backend
sudo systemctl start videoapp-backend
```

#### 前端部署

1. **构建前端**

```bash
cd frontend
npm install
npm run build
```

2. **配置Nginx**

创建 `/etc/nginx/sites-available/videoapp-frontend`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/videoapp/frontend;
    index index.html;

    # 客户端最大上传大小
    client_max_body_size 5G;

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API代理到后端
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    # WebSocket代理
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # 文件代理
    location ~ ^/(uploads|outputs|thumbnails)/ {
        proxy_pass http://localhost:8000;
        proxy_buffering off;
    }

    # SPA路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

3. **部署前端文件**

```bash
sudo mkdir -p /var/www/videoapp
sudo cp -r frontend/dist/* /var/www/videoapp/frontend/
sudo chown -R www-data:www-data /var/www/videoapp
```

4. **启用Nginx配置**

```bash
sudo ln -s /etc/nginx/sites-available/videoapp-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## ⚙️ 环境变量配置 / Environment Variables

### 后端环境变量

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `DEBUG` | 调试模式 | `true` | 否 |
| `HOST` | 监听地址 | `0.0.0.0` | 否 |
| `PORT` | 监听端口 | `8000` | 否 |
| `APP_NAME` | 应用名称 | `视频水印去除工具` | 否 |
| `APP_VERSION` | 应用版本 | `1.0.0` | 否 |
| `DATABASE_URL` | 数据库连接 | `sqlite+aiosqlite:///./video_platform.db` | 是 |
| `UPLOAD_DIR` | 上传目录 | `uploads` | 否 |
| `OUTPUT_DIR` | 输出目录 | `outputs` | 否 |
| `THUMBNAIL_DIR` | 缩略图目录 | `thumbnails` | 否 |
| `MAX_FILE_SIZE` | 最大文件大小（字节） | `5368709120` (5GB) | 否 |
| `MAX_BATCH_UPLOAD` | 批量上传最大数量 | `50` | 否 |
| `MAX_PARALLEL_UPLOAD` | 并行上传数量 | `5` | 否 |
| `MAX_PARALLEL_PROCESS` | 并行处理数量 | `3` | 否 |
| `SUPPORTED_FORMATS` | 支持的视频格式 | `mp4,avi,mov,mkv` | 否 |

### 前端环境变量

前端通过Vite配置文件管理环境变量，主要配置在 `vite.config.ts` 中。

## 🚄 性能优化 / Performance Optimization

### 1. 后端优化

#### Worker数量调整

根据CPU核心数调整Gunicorn worker数量：

```bash
# 推荐公式: workers = (2 × CPU核心数) + 1
gunicorn app.main:app \
    --workers 9 \  # 假设4核CPU
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

#### 并发处理优化

编辑 `.env` 文件：

```bash
# 增加并行处理数量（根据服务器性能）
MAX_PARALLEL_UPLOAD=10
MAX_PARALLEL_PROCESS=5
```

#### FFmpeg硬件加速

如果服务器支持GPU，配置FFmpeg使用硬件编码：

```bash
# 检查硬件加速支持
ffmpeg -hwaccels

# 在代码中使用硬件加速（需要修改watermark_removal.py）
# -hwaccel cuda -hwaccel_output_format cuda
```

### 2. 前端优化

前端已经配置了以下优化：

- ✅ 代码分割（React、Ant Design、工具库分离）
- ✅ Tree Shaking（移除未使用的代码）
- ✅ 压缩（Terser压缩，移除console和debugger）
- ✅ 资源优化（CSS代码分割）

### 3. Nginx优化

#### 启用Gzip压缩

```nginx
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript 
           application/json application/javascript application/xml+rss;
```

#### 配置缓存

```nginx
# 静态资源缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# API响应不缓存
location /api/ {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

### 4. 数据库优化

#### 使用PostgreSQL（推荐生产环境）

```bash
# 安装PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb videoapp
sudo -u postgres createuser videoapp

# 配置环境变量
DATABASE_URL=postgresql+asyncpg://videoapp:password@localhost/videoapp
```

#### 定期清理

```bash
# 清理旧的处理任务记录
# 添加到crontab
0 2 * * * python3 /path/to/cleanup_script.py
```

## 📊 监控和维护 / Monitoring & Maintenance

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 前端健康检查
curl http://localhost/health
```

### 日志管理

#### 查看日志

```bash
# Docker Compose日志
docker-compose logs -f backend
docker-compose logs -f frontend

# Systemd日志
journalctl -u videoapp-backend -f
```

#### 日志轮转

创建 `/etc/logrotate.d/videoapp`:

```
/var/log/videoapp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 videoapp videoapp
    sharedscripts
}
```

### 备份策略

```bash
# 备份脚本
#!/bin/bash
BACKUP_DIR="/backup/videoapp"
DATE=$(date +%Y%m%d)

# 备份数据库
cp /path/to/video_platform.db $BACKUP_DIR/db_$DATE.db

# 备份视频文件
tar -czf $BACKUP_DIR/videos_$DATE.tar.gz /path/to/uploads /path/to/outputs

# 删除30天前的备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

添加到crontab：
```bash
0 2 * * * /path/to/backup.sh
```

### 监控指标

建议监控以下指标：

- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络流量
- API响应时间
- 错误率
- 活跃任务数

## 🔧 故障排查 / Troubleshooting

### 常见问题

#### 1. 容器无法启动

```bash
# 查看容器日志
docker-compose logs backend
docker-compose logs frontend

# 检查端口占用
sudo lsof -i :8000
sudo lsof -i :80

# 重新构建
docker-compose down
docker-compose up -d --build
```

#### 2. 文件上传失败

```bash
# 检查磁盘空间
df -h

# 检查文件大小限制
# 编辑 .env 文件
MAX_FILE_SIZE=10737418240  # 10GB

# 检查Nginx配置
# client_max_body_size 10G;
```

#### 3. 视频处理缓慢

```bash
# 检查CPU使用率
top

# 增加并行处理数量
MAX_PARALLEL_PROCESS=5

# 检查FFmpeg性能
time ffmpeg -i input.mp4 -c copy output.mp4
```

#### 4. WebSocket连接失败

```bash
# 检查Nginx WebSocket配置
# 确保包含:
# proxy_http_version 1.1;
# proxy_set_header Upgrade $http_upgrade;
# proxy_set_header Connection "upgrade";

# 检查防火墙
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

#### 5. 前端无法访问后端API

```bash
# 检查后端服务状态
curl http://localhost:8000/health

# 检查Nginx代理配置
sudo nginx -t

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log
```

### 调试模式

开启调试模式获取更多信息：

```bash
# 后端
DEBUG=true

# 查看详细日志
docker-compose logs -f backend
```

## 🔒 安全建议 / Security

1. **使用HTTPS**: 生产环境必须启用SSL/TLS
2. **限制文件类型**: 只允许视频格式上传
3. **文件大小限制**: 设置合理的限制
4. **防火墙配置**: 只开放必要的端口
5. **定期更新**: 保持系统和依赖更新
6. **备份策略**: 定期备份数据
7. **日志审计**: 定期检查日志
8. **访问控制**: 实现认证和授权机制

## 📚 相关文档 / Related Documentation

- [README.md](./README.md) - 项目概述和快速开始
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API详细文档
- [FAQ.md](./FAQ.md) - 常见问题解答

## 💬 支持 / Support

如有问题，请：
1. 查看本文档的故障排查部分
2. 查看FAQ文档
3. 提交Issue到项目仓库

---

**最后更新**: 2024-01-15
