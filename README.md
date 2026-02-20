# 视频水印去除工具 / Video Watermark Remover

一个基于AI的视频处理系统，提供水印检测、智能去除和视频优化功能。

An AI-powered video processing system that provides watermark detection, intelligent removal, and video optimization features.

## 📋 目录 / Table of Contents

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [安装指南](#安装指南)
- [使用说明](#使用说明)
- [API文档](#api文档)
- [部署指南](#部署指南)
- [常见问题](#常见问题)

## ✨ 功能特性 / Features

### 核心功能

- **视频导入**
  - 本地视频上传（支持MP4、AVI、MOV、MKV格式）
  - URL视频下载（支持YouTube、Bilibili等主流平台）
  - 批量上传（最多50个文件）
  - 自动提取视频元数据

- **水印检测**
  - 手动标记水印区域
  - 视频帧预览
  - 多区域标记支持
  - 批量检测功能

- **水印去除**
  - 裁剪重构模式（智能裁剪去除边缘水印）
  - 异步任务处理
  - 实时进度推送
  - 批量处理支持

- **批量处理**
  - 批量上传（并行上传最多5个文件）
  - 批量检测（并行处理最多3个视频）
  - 批量去除
  - 统一进度管理

- **实时通信**
  - WebSocket实时进度推送
  - 任务状态更新
  - 错误通知

## 🛠 技术栈 / Tech Stack

### 后端 / Backend

- **框架**: FastAPI + Python 3.10+
- **视频处理**: FFmpeg, OpenCV
- **视频下载**: yt-dlp
- **数据库**: SQLite + SQLAlchemy
- **异步处理**: asyncio
- **实时通信**: WebSocket

### 前端 / Frontend

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Ant Design
- **HTTP客户端**: Axios
- **路由**: React Router
- **状态管理**: React Context + Hooks

### 部署 / Deployment

- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx
- **反向代理**: Nginx

## 🏗 系统架构 / Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         用户界面 / UI                         │
│                    (React + Ant Design)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理                           │
│                   (静态文件 + API代理)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
┌───────────────────────┐     ┌───────────────────────┐
│   静态文件服务         │     │   FastAPI 后端         │
│   (React Build)       │     │   (Python)            │
└───────────────────────┘     └───────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
          ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
          │  视频导入模块    │   │  水印检测模块    │   │  水印去除模块    │
          │  (Upload/URL)   │   │  (Detection)    │   │  (Removal)      │
          └─────────────────┘   └─────────────────┘   └─────────────────┘
                    │                     │                     │
                    └─────────────────────┼─────────────────────┘
                                          ▼
                              ┌───────────────────────┐
                              │   FFmpeg + OpenCV     │
                              │   (视频处理引擎)       │
                              └───────────────────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │   SQLite 数据库        │
                              │   (元数据存储)         │
                              └───────────────────────┘
```

## 🚀 快速开始 / Quick Start

### 使用 Docker Compose（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd video-watermark-remover

# 启动服务
cd backend
docker-compose up -d

# 访问应用
# 前端: http://localhost
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

## 📦 安装指南 / Installation Guide

### 系统要求

- **操作系统**: Linux, macOS, Windows
- **Docker**: 20.10+ (推荐使用Docker部署)
- **Docker Compose**: 1.29+
- **Python**: 3.10+ (本地开发)
- **Node.js**: 18+ (本地开发)
- **FFmpeg**: 4.0+ (本地开发)

### 后端安装

1. **安装系统依赖**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg python3.10 python3-pip

# macOS
brew install ffmpeg python@3.10

# Windows
# 下载并安装 FFmpeg: https://ffmpeg.org/download.html
# 下载并安装 Python: https://www.python.org/downloads/
```

2. **安装Python依赖**

```bash
cd backend
pip install -r requirements.txt
```

3. **配置环境变量**

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要参数
```

4. **初始化数据库**

```bash
# 数据库会在首次启动时自动创建
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

## 📖 使用说明 / Usage Guide

### 1. 上传视频

#### 本地上传
1. 访问"视频上传"页面
2. 点击上传区域或拖拽文件
3. 支持单个或批量上传（最多50个）
4. 等待上传完成

#### URL下载
1. 在上传页面输入视频URL
2. 点击"下载"按钮
3. 系统自动下载并导入视频

### 2. 标记水印

1. 在视频列表中选择视频
2. 点击"标记水印"按钮
3. 在视频帧上拖拽绘制矩形框
4. 可以标记多个水印区域
5. 点击"保存"确认标记

### 3. 去除水印

1. 选择已标记水印的视频
2. 点击"去除水印"按钮
3. 选择处理模式（裁剪重构）
4. 设置裁剪参数
5. 点击"开始处理"
6. 实时查看处理进度
7. 处理完成后下载结果

### 4. 批量处理

1. 在视频列表中选择多个视频
2. 点击"批量处理"按钮
3. 统一设置处理参数
4. 开始批量处理
5. 查看每个视频的处理状态
6. 批量下载处理结果

## 📚 API文档 / API Documentation

详细的API文档请参考：[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

### 快速参考

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要端点

```
POST   /api/videos/upload          # 上传视频
POST   /api/videos/batch-upload    # 批量上传
POST   /api/videos/download         # URL下载
GET    /api/videos                  # 获取视频列表
GET    /api/videos/{video_id}       # 获取视频详情
DELETE /api/videos/{video_id}       # 删除视频

GET    /api/videos/{video_id}/frames           # 获取视频帧
POST   /api/videos/{video_id}/watermarks       # 标记水印
GET    /api/videos/{video_id}/watermarks       # 获取水印列表
PUT    /api/videos/{video_id}/watermarks/{id}  # 更新水印
DELETE /api/videos/{video_id}/watermarks/{id}  # 删除水印

POST   /api/videos/{video_id}/remove  # 去除水印
POST   /api/batch/remove              # 批量去除
GET    /api/tasks/{task_id}           # 获取任务状态
GET    /api/tasks                     # 获取任务列表

WS     /ws/{client_id}                # WebSocket连接
```

## 🚢 部署指南 / Deployment Guide

详细的部署文档请参考：[DEPLOYMENT.md](./DEPLOYMENT.md)

### Docker Compose 部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd video-watermark-remover

# 2. 配置环境变量
cd backend
cp .env.example .env
# 编辑 .env 文件

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 停止服务
docker-compose down
```

### 生产环境配置

1. **配置域名和HTTPS**
   - 使用Nginx配置SSL证书
   - 配置域名解析

2. **配置文件存储**
   - 使用持久化卷存储视频文件
   - 配置备份策略

3. **性能优化**
   - 调整Worker数量
   - 配置缓存策略
   - 启用CDN加速

4. **监控和日志**
   - 配置日志收集
   - 设置监控告警
   - 定期备份数据

## ❓ 常见问题 / FAQ

详细的FAQ请参考：[FAQ.md](./FAQ.md)

### 快速问答

**Q: 支持哪些视频格式？**
A: 支持MP4、AVI、MOV、MKV格式。

**Q: 单个文件大小限制是多少？**
A: 默认限制为5GB，可以在配置文件中修改。

**Q: 批量上传最多支持多少个文件？**
A: 最多支持50个文件同时上传。

**Q: 处理速度如何？**
A: 取决于视频大小和服务器性能，一般1GB视频需要2-5分钟。

**Q: 如何查看处理进度？**
A: 系统通过WebSocket实时推送处理进度，在任务管理页面可以查看。

**Q: 处理失败怎么办？**
A: 查看任务详情中的错误信息，常见问题包括视频格式不支持、文件损坏等。

## 📄 许可证 / License

MIT License

## 🤝 贡献 / Contributing

欢迎提交Issue和Pull Request！

## 📧 联系方式 / Contact

如有问题或建议，请提交Issue。

---

**注意**: 本工具仅用于处理用户拥有合法版权的视频，请勿用于侵权行为。
