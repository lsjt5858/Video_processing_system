"""
FastAPI应用入口
"""
import os
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .database import init_db, close_db

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 创建必要的目录
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
THUMBNAIL_DIR = BASE_DIR / "thumbnails"

for directory in [UPLOAD_DIR, OUTPUT_DIR, THUMBNAIL_DIR]:
    directory.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时初始化数据库，关闭时清理资源
    """
    # 启动时执行
    print("应用启动中...")
    await init_db()
    print("数据库初始化完成")
    
    yield
    
    # 关闭时执行
    print("应用关闭中...")
    await close_db()
    print("数据库连接已关闭")


app = FastAPI(
    title="视频水印去除工具",
    description="AI驱动的视频处理系统，提供水印检测和智能去除功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该配置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
app.mount("/thumbnails", StaticFiles(directory=str(THUMBNAIL_DIR)), name="thumbnails")

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()


@app.get("/")
async def root():
    """根路径"""
    return {"message": "视频水印去除工具 API"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "upload_dir": str(UPLOAD_DIR),
        "output_dir": str(OUTPUT_DIR),
        "thumbnail_dir": str(THUMBNAIL_DIR)
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket端点，用于实时推送进度更新
    
    参数:
        client_id: 客户端唯一标识
    """
    await manager.connect(client_id, websocket)
    try:
        while True:
            # 接收客户端消息（保持连接）
            data = await websocket.receive_text()
            # 可以在这里处理客户端发送的消息
            await manager.send_message(client_id, {
                "type": "pong",
                "message": "连接正常"
            })
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"客户端 {client_id} 断开连接")


# 导入视频上传模块
from fastapi import File, UploadFile as FastAPIUploadFile
from typing import List as TypingList
from pydantic import BaseModel
from .video_import import (
    upload_single_video,
    upload_batch_videos,
    download_video_from_url,
    FileSizeExceededError,
    UnsupportedFormatError,
    InvalidUrlError,
    VideoNotAccessibleError
)


@app.post("/api/videos/upload")
async def upload_video(
    file: FastAPIUploadFile = File(...),
    user_id: str = "default_user"
):
    """
    上传单个视频文件
    
    参数:
        file: 视频文件
        user_id: 用户ID（可选）
        
    返回:
        VideoImportResult: 导入结果
    """
    try:
        result = await upload_single_video(file, user_id)
        return {
            "success": True,
            "data": {
                "video_id": result.video_id,
                "filename": file.filename,
                "file_size": result.metadata.file_size,
                "format": result.metadata.format,
                "storage_path": result.storage_path,
                "import_time": result.import_time.isoformat()
            }
        }
    except FileSizeExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e)
        )
    except UnsupportedFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )


@app.post("/api/videos/batch-upload")
async def batch_upload_videos(
    files: TypingList[FastAPIUploadFile] = File(...),
    user_id: str = "default_user",
    client_id: str = None
):
    """
    批量上传视频文件（支持并发和进度推送）
    
    参数:
        files: 视频文件列表（最多50个）
        user_id: 用户ID（可选）
        client_id: 客户端ID，用于WebSocket进度推送（可选）
        
    返回:
        dict: 批量上传结果
    """
    try:
        # 如果提供了client_id，使用WebSocket推送进度
        websocket_callback = manager.send_message if client_id else None
        
        results = await upload_batch_videos(
            files=files,
            user_id=user_id,
            websocket_callback=websocket_callback,
            client_id=client_id
        )
        return {
            "success": True,
            "data": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量上传失败: {str(e)}"
        )



# 定义请求模型
class VideoDownloadRequest(BaseModel):
    url: str
    user_id: str = "default_user"
    client_id: str = None  # 用于WebSocket进度推送


@app.post("/api/videos/download")
async def download_video(request: VideoDownloadRequest):
    """
    通过URL下载视频
    
    参数:
        request: 包含视频URL和用户ID的请求体
        
    返回:
        VideoImportResult: 导入结果
    """
    try:
        # 如果提供了client_id，使用WebSocket推送进度
        websocket_callback = manager.send_message if request.client_id else None
        
        result = await download_video_from_url(
            url=request.url,
            user_id=request.user_id,
            websocket_callback=websocket_callback,
            client_id=request.client_id
        )
        
        return {
            "success": True,
            "data": {
                "video_id": result.video_id,
                "url": request.url,
                "file_size": result.metadata.file_size,
                "format": result.metadata.format,
                "resolution": result.metadata.resolution,
                "duration": result.metadata.duration,
                "storage_path": result.storage_path,
                "import_time": result.import_time.isoformat()
            }
        }
    except InvalidUrlError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except VideoNotAccessibleError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnsupportedFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载失败: {str(e)}"
        )
