# 后端部署配置说明

本目录包含视频水印去除工具后端的完整部署配置文件。

## 📁 文件清单

### 核心配置文件

| 文件 | 说明 | 用途 |
|------|------|------|
| `Dockerfile` | Docker镜像构建文件 | 容器化部署 |
| `docker-compose.yml` | Docker编排配置 | 一键启动容器服务 |
| `.env.example` | 环境变量模板 | 开发环境配置参考 |
| `.env.production` | 生产环境配置模板 | 生产环境配置参考 |
| `.dockerignore` | Docker构建忽略文件 | 优化镜像大小 |

### 启动脚本

| 文件 | 说明 | 使用场景 |
|------|------|----------|
| `run.sh` | 开发环境启动脚本 | 本地开发和测试 |
| `start-production.sh` | 生产环境启动脚本 | 生产环境部署 |
| `stop-production.sh` | 生产环境停止脚本 | 停止生产服务 |
| `backup.sh` | 备份脚本 | 数据备份 |

### 文档

| 文件 | 说明 |
|------|------|
| `DEPLOYMENT.md` | 详细部署指南 |
| `QUICKSTART.md` | 快速开始指南 |
| `DEPLOYMENT_README.md` | 本文件 |

## 🚀 快速开始

### 1. 本地开发

```bash
# 一键启动
./run.sh
```

访问: http://localhost:8000

### 2. Docker部署

```bash
# 配置环境变量
cp .env.example .env

# 启动服务
docker-compose up -d
```

### 3. 生产部署

```bash
# 配置生产环境
cp .env.production .env
nano .env  # 编辑配置

# 启动服务
./start-production.sh
```

## 📋 部署检查清单

### 部署前

- [ ] 检查Python版本 (3.10+)
- [ ] 安装FFmpeg
- [ ] 配置环境变量
- [ ] 检查磁盘空间 (建议100GB+)
- [ ] 检查端口可用性 (8000)

### 部署后

- [ ] 验证健康检查: `curl http://localhost:8000/health`
- [ ] 测试视频上传
- [ ] 检查日志输出
- [ ] 配置备份任务
- [ ] 设置监控告警

## 🔧 配置说明

### 环境变量优先级

1. `.env` - 当前环境配置（优先级最高）
2. `.env.production` - 生产环境模板
3. `.env.example` - 开发环境模板

### 关键配置项

#### 性能配置

```bash
# 并行处理数量（根据CPU核心数调整）
MAX_PARALLEL_PROCESS=3

# Worker进程数（生产环境）
WORKERS=4
```

#### 安全配置

```bash
# 关闭调试模式（生产环境必须）
DEBUG=false

# 配置CORS
CORS_ORIGINS=https://yourdomain.com

# 设置API密钥
API_KEY=your-secure-key
```

#### 存储配置

```bash
# 文件大小限制（5GB）
MAX_FILE_SIZE=5368709120

# 存储目录
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
```

## 🐳 Docker配置

### Dockerfile特性

- **基础镜像**: Python 3.10-slim
- **系统依赖**: FFmpeg, OpenCV依赖
- **健康检查**: 30秒间隔
- **端口**: 8000
- **工作目录**: /app

### docker-compose.yml特性

- **持久化存储**: 视频文件和数据库
- **自动重启**: unless-stopped
- **健康检查**: 内置
- **网络**: 独立bridge网络

### 常用Docker命令

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec backend bash

# 查看资源使用
docker stats
```

## 📊 监控和维护

### 健康检查

```bash
# HTTP健康检查
curl http://localhost:8000/health

# 预期响应
{"status":"healthy"}
```

### 日志管理

```bash
# 查看应用日志
tail -f logs/error.log
tail -f logs/access.log

# 查看Docker日志
docker-compose logs -f backend

# 查看系统服务日志
journalctl -u videoapp -f
```

### 备份

```bash
# 手动备份
./backup.sh

# 自动备份（添加到crontab）
0 2 * * * cd /path/to/backend && ./backup.sh
```

### 性能监控

```bash
# 检查CPU和内存
top
htop

# 检查磁盘使用
df -h

# 检查进程
ps aux | grep uvicorn
ps aux | grep gunicorn
```

## 🔒 安全建议

### 生产环境必做

1. **关闭调试模式**: `DEBUG=false`
2. **启用HTTPS**: 配置SSL证书
3. **设置防火墙**: 只开放必要端口
4. **配置CORS**: 限制允许的源
5. **使用强密码**: API密钥、数据库密码
6. **定期更新**: 系统和依赖包
7. **备份策略**: 定期备份数据
8. **日志审计**: 定期检查日志

### 可选安全措施

- 启用API认证（JWT或API Key）
- 配置速率限制
- 使用WAF（Web应用防火墙）
- 启用入侵检测
- 配置安全头（Nginx）

## 🎯 性能优化

### 应用层

- 增加Worker进程数
- 启用缓存（Redis）
- 优化数据库查询
- 使用连接池

### 系统层

- 使用SSD存储
- 增加内存
- 启用FFmpeg硬件加速
- 配置Nginx缓存

### 网络层

- 使用CDN
- 启用Gzip压缩
- 配置HTTP/2
- 优化TCP参数

## 🐛 故障排查

### 常见问题

#### 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :8000

# 检查日志
tail -f logs/error.log

# 检查权限
ls -la
```

#### 视频上传失败

```bash
# 检查磁盘空间
df -h

# 检查文件大小限制
grep MAX_FILE_SIZE .env

# 检查Nginx配置
nginx -t
```

#### 处理缓慢

```bash
# 检查CPU使用
top

# 增加并行处理数
# 编辑 .env
MAX_PARALLEL_PROCESS=5

# 检查FFmpeg性能
ffmpeg -hwaccels
```

### 调试模式

```bash
# 启用调试模式
echo "DEBUG=true" >> .env

# 重启服务
./stop-production.sh
./start-production.sh

# 查看详细日志
tail -f logs/error.log
```

## 📚 相关文档

- [DEPLOYMENT.md](DEPLOYMENT.md) - 详细部署指南
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [README.md](README.md) - 项目说明
- [API文档](http://localhost:8000/docs) - 在线API文档

## 🆘 获取帮助

### 文档资源

- **API文档**: http://localhost:8000/docs
- **部署指南**: DEPLOYMENT.md
- **快速开始**: QUICKSTART.md

### 社区支持

- GitHub Issues
- 技术论坛
- 邮件支持

## 📝 更新日志

### v1.0.0 (2024-01-15)

- ✅ 初始部署配置
- ✅ Docker支持
- ✅ 生产环境脚本
- ✅ 健康检查
- ✅ 备份脚本
- ✅ 完整文档

---

**最后更新**: 2024-01-15
**维护者**: 开发团队
