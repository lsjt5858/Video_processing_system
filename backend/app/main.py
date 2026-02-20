"""
FastAPI应用入口
"""
import os
import uuid
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
from typing import List as TypingList, Optional
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


# 导入水印检测模块
from .watermark_detection import (
    batch_extract_frames,
    batch_mark_watermarks,
    FrameExtractionError
)
from .database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends


# 定义批量检测请求模型
class BatchDetectRequest(BaseModel):
    video_ids: TypingList[str]
    num_frames: int = 10


@app.post("/api/batch/detect")
async def batch_detect(
    request: BatchDetectRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    批量检测水印（提取所有视频的预览帧）
    
    参数:
        request: 包含视频ID列表和帧数的请求体
        db: 数据库会话
        
    返回:
        dict: 批量检测结果，包含所有视频的预览帧
    """
    try:
        from . import crud
        
        # 获取所有视频的路径
        video_paths = []
        for video_id in request.video_ids:
            video = await crud.get_video_by_id(db, video_id)
            if video:
                video_paths.append((video_id, video.storage_path))
        
        if not video_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到任何有效的视频"
            )
        
        # 批量提取预览帧
        results = await batch_extract_frames(
            video_paths=video_paths,
            num_frames=request.num_frames
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
            detail=f"批量检测失败: {str(e)}"
        )


# 定义批量标记请求模型
class BatchMarkRequest(BaseModel):
    watermark_data: TypingList[dict]  # 每个元素包含 video_id 和 bounding_boxes


@app.post("/api/batch/mark")
async def batch_mark(
    request: BatchMarkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    批量标记水印区域
    
    参数:
        request: 包含多个视频的水印标记数据
        db: 数据库会话
        
    返回:
        dict: 批量标记结果
    """
    try:
        from . import crud
        
        # 为每个视频添加video_path
        enriched_data = []
        for data in request.watermark_data:
            video_id = data.get("video_id")
            video = await crud.get_video_by_id(db, video_id)
            
            if not video:
                enriched_data.append({
                    "video_id": video_id,
                    "video_path": None,
                    "bounding_boxes": data.get("bounding_boxes", [])
                })
            else:
                enriched_data.append({
                    "video_id": video_id,
                    "video_path": video.storage_path,
                    "bounding_boxes": data.get("bounding_boxes", [])
                })
        
        # 批量标记水印
        results = await batch_mark_watermarks(
            db=db,
            watermark_data=enriched_data
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
            detail=f"批量标记失败: {str(e)}"
        )


# 导入任务处理模块
from .task_processor import task_processor
from . import crud


# 定义批量去除请求模型
class BatchRemovalRequest(BaseModel):
    removal_tasks: TypingList[dict]  # 每个元素包含 video_id 和 regions
    user_id: str = "default_user"
    client_id: Optional[str] = None  # 用于WebSocket进度推送


@app.post("/api/batch/remove")
async def batch_remove(
    request: BatchRemovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    批量执行水印去除（最多3个视频并行）
    
    参数:
        request: 包含多个视频的去除任务数据
        db: 数据库会话
        
    返回:
        dict: 批量去除结果，包含job_id和初始状态
    """
    try:
        # 生成批量任务ID
        job_id = f"batch_{uuid.uuid4().hex[:12]}"
        
        # 准备批量任务数据
        batch_tasks = []
        task_ids = []
        
        for task_data in request.removal_tasks:
            video_id = task_data.get("video_id")
            regions = task_data.get("regions", [])
            
            # 获取视频信息
            video = await crud.get_video_by_id(db, video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"视频 {video_id} 不存在"
                )
            
            # 创建处理任务记录
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            task_ids.append(task_id)
            
            await crud.create_processing_task(
                db=db,
                task_id=task_id,
                user_id=request.user_id,
                video_id=video_id,
                task_type="removal",
                status="pending",
                parameters={
                    "mode": "crop_reconstruct",
                    "regions": regions,
                    "job_id": job_id
                }
            )
            
            # 准备视频元数据
            video_metadata = {
                "resolution_width": video.resolution_width,
                "resolution_height": video.resolution_height,
                "duration": video.duration,
                "codec": video.codec,
                "framerate": video.framerate
            }
            
            # 添加到批量任务列表
            batch_tasks.append({
                "task_id": task_id,
                "video_id": video_id,
                "video_path": video.storage_path,
                "regions": regions,
                "video_metadata": video_metadata
            })
        
        await db.commit()
        
        # 如果提供了client_id，使用WebSocket推送进度
        websocket_callback = manager.send_message if request.client_id else None
        
        # 异步执行批量处理（不等待完成）
        import asyncio
        asyncio.create_task(
            task_processor.process_batch_removal(
                db=db,
                batch_tasks=batch_tasks,
                websocket_callback=websocket_callback,
                client_id=request.client_id
            )
        )
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "task_ids": task_ids,
                "total_count": len(batch_tasks),
                "status": "processing",
                "message": f"批量处理已启动，共 {len(batch_tasks)} 个视频"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量去除失败: {str(e)}"
        )


@app.get("/api/batch/{job_id}")
async def get_batch_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取批量任务状态
    
    参数:
        job_id: 批量任务ID
        db: 数据库会话
        
    返回:
        dict: 批量任务状态信息
    """
    try:
        # 查询所有属于该批量任务的处理任务
        from sqlalchemy import select
        from .database import ProcessingTask as DBProcessingTask
        
        stmt = select(DBProcessingTask).where(
            DBProcessingTask.parameters.op('->>')('job_id') == job_id
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"批量任务 {job_id} 不存在"
            )
        
        # 统计任务状态
        total_count = len(tasks)
        completed_count = sum(1 for t in tasks if t.status == "completed")
        failed_count = sum(1 for t in tasks if t.status == "failed")
        processing_count = sum(1 for t in tasks if t.status == "processing")
        pending_count = sum(1 for t in tasks if t.status == "pending")
        
        # 确定整体状态
        if completed_count == total_count:
            overall_status = "completed"
        elif failed_count == total_count:
            overall_status = "failed"
        elif completed_count + failed_count == total_count:
            overall_status = "completed_with_errors"
        else:
            overall_status = "processing"
        
        # 构建任务详情列表
        task_details = []
        for task in tasks:
            task_details.append({
                "task_id": task.task_id,
                "video_id": task.video_id,
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error_message": task.error_message,
                "result": task.result
            })
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "status": overall_status,
                "total_count": total_count,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "processing_count": processing_count,
                "pending_count": pending_count,
                "tasks": task_details
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取批量任务状态失败: {str(e)}"
        )
