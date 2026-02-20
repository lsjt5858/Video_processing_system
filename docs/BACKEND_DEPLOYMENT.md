# 部署指南

本文档提供视频水印去除工具后端的完整部署指南，包括本地开发、Docker部署和生产环境部署。

## 目录

- [系统要求](#系统要求)
- [本地开发部署](#本地开发部署)
- [Docker部署](#docker部署)
- [生产环境部署](#生产环境部署)
- [环境变量配置](#环境变量配置)
- [健康检查](#健康检查)
- [故障排查](#故障排查)

## 系统要求

### 硬件要求

- **CPU**: 4核心或以上（推荐8核心）
- **内存**: 8GB或以上（推荐16GB）
- **存储**: 100GB或以上可用空间（用于视频文件存储）
- **网络**: 稳定的网络连接（用于视频下载）

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+) / macOS 10.15+ / Windows 10+
- **Python**: 3.10 或更高版本
- **FFmpeg**: 4.0 或更高版本
- **Docker**: 20.10+ (可选，用于容器化部署)
- **Docker Compose**: 1.29+ (可选，用于容器化部署)

## 本地开发部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd backend
```

### 2. 安装系统依赖

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3-pip ffmpeg
```

#### CentOS/RHEL

```bash
sudo yum install -y python3 python3-pip ffmpeg
```

#### macOS

```bash
brew install python@3.10 ffmpeg
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（可选）
nano .env
```

### 4. 启动开发服务器

```bash
# 赋予执行权限
chmod +x run.sh

# 启动服务
./run.sh
```

服务将在 `http://localhost:8000` 启动。

访问 `http://localhost:8000/docs` 查看API文档。

### 5. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应
{"status": "healthy"}
```

## Docker部署

Docker部署提供了隔离的运行环境，简化了依赖管理。

### 1. 安装Docker和Docker Compose

#### Ubuntu

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo apt-get install docker-compose-plugin
```

#### macOS/Windows

下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（根据需要调整）
nano .env
```

### 3. 构建和启动容器

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 健康检查
curl http://localhost:8000/health
```

### 5. 管理容器

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f backend

# 进入容器
docker-compose exec backend bash
```

## 生产环境部署

生产环境部署需要更多的配置和优化，以确保稳定性和性能。

### 1. 准备服务器

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装必要的软件
sudo apt-get install -y python3.10 python3.10-venv python3-pip ffmpeg nginx certbot
```

### 2. 创建应用用户

```bash
# 创建专用用户
sudo useradd -m -s /bin/bash videoapp
sudo usermod -aG sudo videoapp

# 切换到应用用户
sudo su - videoapp
```

### 3. 部署应用

```bash
# 克隆项目
git clone <repository-url>
cd backend

# 配置环境变量
cp .env.example .env
nano .env  # 编辑生产环境配置
```

**重要配置项**:

```bash
# 关闭调试模式
DEBUG=false

# 设置生产数据库（如果使用PostgreSQL）
# DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname

# 配置CORS（设置前端域名）
# CORS_ORIGINS=https://yourdomain.com
```

### 4. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装Gunicorn（生产服务器）
pip install gunicorn
```

### 5. 启动生产服务

```bash
# 赋予执行权限
chmod +x start-production.sh stop-production.sh

# 启动服务
./start-production.sh
```

### 6. 配置Nginx反向代理

创建Nginx配置文件 `/etc/nginx/sites-available/videoapp`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 客户端最大上传大小（5GB）
    client_max_body_size 5G;

    # 超时设置
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态文件（如果需要）
    location /static {
        alias /home/videoapp/backend/static;
    }
}
```

启用配置:

```bash
sudo ln -s /etc/nginx/sites-available/videoapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. 配置SSL证书（推荐）

```bash
# 使用Let's Encrypt获取免费SSL证书
sudo certbot --nginx -d yourdomain.com
```

### 8. 配置系统服务（Systemd）

创建服务文件 `/etc/systemd/system/videoapp.service`:

```ini
[Unit]
Description=Video Watermark Removal Backend
After=network.target

[Service]
Type=simple
User=videoapp
WorkingDirectory=/home/videoapp/backend
Environment="PATH=/home/videoapp/backend/venv/bin"
ExecStart=/home/videoapp/backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /home/videoapp/backend/logs/access.log \
    --error-logfile /home/videoapp/backend/logs/error.log \
    --log-level info \
    --timeout 300
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable videoapp
sudo systemctl start videoapp
sudo systemctl status videoapp
```

### 9. 配置日志轮转

创建日志轮转配置 `/etc/logrotate.d/videoapp`:

```
/home/videoapp/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 videoapp videoapp
    sharedscripts
    postrotate
        systemctl reload videoapp > /dev/null 2>&1 || true
    endscript
}
```

### 10. 配置防火墙

```bash
# 允许HTTP和HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 如果直接访问应用端口
sudo ufw allow 8000/tcp

# 启用防火墙
sudo ufw enable
```

## 环境变量配置

详细的环境变量说明请参考 `.env.example` 文件。

### 核心配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `DEBUG` | 调试模式 | `true` | 否 |
| `HOST` | 监听地址 | `0.0.0.0` | 否 |
| `PORT` | 监听端口 | `8000` | 否 |
| `DATABASE_URL` | 数据库连接 | `sqlite+aiosqlite:///./video_platform.db` | 是 |
| `MAX_FILE_SIZE` | 最大文件大小 | `5368709120` (5GB) | 否 |

### 性能配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MAX_BATCH_UPLOAD` | 批量上传最大数量 | `50` |
| `MAX_PARALLEL_UPLOAD` | 并行上传数量 | `5` |
| `MAX_PARALLEL_PROCESS` | 并行处理数量 | `3` |

### 安全配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `CORS_ORIGINS` | CORS允许的源 | `https://yourdomain.com` |
| `API_KEY` | API密钥 | `your-secret-key` |

## 健康检查

应用提供了健康检查端点用于监控服务状态。

### 健康检查端点

```bash
GET /health
```

**响应示例**:

```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0"
}
```

### 监控脚本

创建监控脚本 `monitor.sh`:

```bash
#!/bin/bash

while true; do
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo "$(date): Service is down, restarting..."
        systemctl restart videoapp
    fi
    sleep 60
done
```

## 故障排查

### 常见问题

#### 1. 服务无法启动

**症状**: 运行启动脚本后服务立即退出

**解决方案**:

```bash
# 检查日志
tail -f logs/error.log

# 检查端口占用
sudo lsof -i :8000

# 检查Python版本
python3 --version

# 检查FFmpeg
ffmpeg -version
```

#### 2. 视频上传失败

**症状**: 上传大文件时失败

**解决方案**:

```bash
# 检查磁盘空间
df -h

# 检查文件大小限制
# 编辑 .env 文件，增加 MAX_FILE_SIZE

# 如果使用Nginx，检查配置
# client_max_body_size 5G;
```

#### 3. 视频处理缓慢

**症状**: 视频处理时间过长

**解决方案**:

```bash
# 检查CPU使用率
top

# 增加并行处理数量
# 编辑 .env 文件
MAX_PARALLEL_PROCESS=5

# 检查FFmpeg性能
ffmpeg -hwaccels  # 查看硬件加速支持
```

#### 4. 数据库错误

**症状**: 数据库连接失败或查询错误

**解决方案**:

```bash
# 检查数据库文件权限
ls -la video_platform.db

# 重新初始化数据库
rm video_platform.db
python3 -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
"
```

#### 5. WebSocket连接失败

**症状**: 实时进度更新不工作

**解决方案**:

```bash
# 检查Nginx WebSocket配置
# 确保包含以下配置:
# proxy_http_version 1.1;
# proxy_set_header Upgrade $http_upgrade;
# proxy_set_header Connection "upgrade";

# 检查防火墙
sudo ufw status
```

### 日志位置

- **应用日志**: `logs/error.log`, `logs/access.log`
- **Nginx日志**: `/var/log/nginx/error.log`, `/var/log/nginx/access.log`
- **系统日志**: `journalctl -u videoapp -f`

### 性能优化建议

1. **使用SSD存储**: 视频文件I/O密集，SSD可显著提升性能
2. **启用FFmpeg硬件加速**: 如果支持GPU，配置FFmpeg使用硬件编码
3. **增加Worker数量**: 根据CPU核心数调整Gunicorn worker数量
4. **使用CDN**: 对于处理后的视频，使用CDN加速下载
5. **数据库优化**: 生产环境建议使用PostgreSQL替代SQLite
6. **缓存策略**: 启用Redis缓存视频元数据和处理结果

### 备份策略

```bash
# 备份数据库
cp video_platform.db backup/video_platform_$(date +%Y%m%d).db

# 备份视频文件
tar -czf backup/videos_$(date +%Y%m%d).tar.gz uploads/ outputs/

# 自动备份脚本（添加到crontab）
0 2 * * * /home/videoapp/backend/backup.sh
```

## 安全建议

1. **使用HTTPS**: 生产环境必须启用SSL/TLS
2. **限制文件类型**: 只允许视频格式上传
3. **文件大小限制**: 设置合理的文件大小限制
4. **API认证**: 实现API密钥或JWT认证
5. **速率限制**: 使用Nginx限制请求频率
6. **定期更新**: 保持系统和依赖包更新
7. **日志审计**: 定期检查访问日志和错误日志
8. **备份策略**: 定期备份数据库和重要文件

## 扩展性建议

### 水平扩展

1. **负载均衡**: 使用Nginx或HAProxy分发请求到多个后端实例
2. **共享存储**: 使用NFS或对象存储（S3/MinIO）共享视频文件
3. **分布式数据库**: 使用PostgreSQL主从复制或集群
4. **消息队列**: 使用Redis或RabbitMQ处理异步任务

### 监控和告警

1. **应用监控**: 使用Prometheus + Grafana监控应用指标
2. **日志聚合**: 使用ELK Stack或Loki聚合日志
3. **告警通知**: 配置邮件或Slack通知
4. **性能分析**: 使用APM工具（如New Relic）分析性能瓶颈

## 支持

如有问题，请查看:

- **API文档**: http://localhost:8000/docs
- **项目README**: ../README.md
- **问题追踪**: GitHub Issues

---

**最后更新**: 2024-01-15
