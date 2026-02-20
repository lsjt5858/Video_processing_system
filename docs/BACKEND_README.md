# 一键美 - 后端

基于FastAPI的视频处理后端服务。

## 功能特性

- 视频上传（本地上传、URL下载、批量上传）
- 水印检测（手动标记）
- 水印去除（裁剪模式）
- 批量处理
- WebSocket实时进度推送

## 技术栈

- FastAPI - Web框架
- FFmpeg - 视频处理
- OpenCV - 图像处理
- yt-dlp - 视频下载
- SQLite - 数据存储
- WebSocket - 实时通信

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 安装FFmpeg

**Windows:**
- 下载FFmpeg: https://ffmpeg.org/download.html
- 解压并添加到系统PATH

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 3. 配置环境变量

复制`.env.example`为`.env`并根据需要修改配置：

```bash
cp .env.example .env
```

### 4. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用启动脚本
chmod +x run.sh
./run.sh
```

服务将在 http://localhost:8000 启动

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend/
├── app/                    # 应用代码
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── models.py          # 数据模型
│   ├── database.py        # 数据库配置
│   ├── crud.py            # 数据库操作
│   ├── video_import.py    # 视频导入
│   ├── watermark_detection.py  # 水印检测
│   ├── watermark_removal.py    # 水印去除
│   ├── task_processor.py  # 任务处理
│   ├── websocket.py       # WebSocket管理
│   └── utils.py           # 工具函数
├── uploads/               # 上传的视频
├── outputs/               # 处理后的视频
├── thumbnails/            # 视频缩略图
├── requirements.txt       # Python依赖
├── .env                   # 环境变量
└── README.md             # 说明文档
```

## 开发说明

### 添加新的API端点

在`app/main.py`中添加路由：

```python
@app.get("/api/example")
async def example():
    return {"message": "example"}
```

### 数据库迁移

项目使用SQLite，数据库文件会在首次运行时自动创建。

## 许可证

MIT
