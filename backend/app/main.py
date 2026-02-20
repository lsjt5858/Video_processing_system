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
    download_video_from_url
)
from .errors import (
    VideoProcessingError,
    FileSizeExceededError,
    UnsupportedFormatError,
    InvalidUrlError,
    VideoNotAccessibleError,
    CorruptedVideoError,
    MetadataExtractionError,
    create_error_response,
    log_error
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
                "resolution": {
                    "width": result.metadata.resolution[0],
                    "height": result.metadata.resolution[1]
                },
                "duration": result.metadata.duration,
                "storage_path": result.storage_path,
                "import_time": result.import_time.isoformat()
            }
        }
    except VideoProcessingError as e:
        log_error(e, {"operation": "upload_video", "filename": file.filename})
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )
    except Exception as e:
        log_error(e, {"operation": "upload_video", "filename": file.filename})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(e)
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
                "resolution": {
                    "width": result.metadata.resolution[0],
                    "height": result.metadata.resolution[1]
                },
                "duration": result.metadata.duration,
                "storage_path": result.storage_path,
                "import_time": result.import_time.isoformat()
            }
        }
    except VideoProcessingError as e:
        log_error(e, {"operation": "download_video", "url": request.url})
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )
    except Exception as e:
        log_error(e, {"operation": "download_video", "url": request.url})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(e)
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


@app.get("/api/videos/{video_id}/frames")
async def get_video_frames(
    video_id: str,
    num_frames: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频帧（用于水印标记）
    
    参数:
        video_id: 视频ID
        num_frames: 要提取的帧数量（默认10帧）
        db: 数据库会话
        
    返回:
        dict: 包含视频帧信息的响应
    """
    try:
        from .watermark_detection import extract_frames_for_preview
        
        # 获取视频信息
        video = await crud.get_video_by_id(db, video_id)
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"视频 {video_id} 不存在"
            )
        
        # 提取视频帧
        frames = await extract_frames_for_preview(
            video_path=video.storage_path,
            video_id=video_id,
            num_frames=num_frames
        )
        
        return {
            "success": True,
            "data": {
                "video_id": video_id,
                "num_frames": len(frames),
                "frames": frames
            }
        }
        
    except HTTPException:
        raise
    except FrameExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提取视频帧失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取视频帧失败: {str(e)}"
        )


# 定义水印标记请求模型
class WatermarkMarkRequest(BaseModel):
    bounding_boxes: TypingList[dict]  # 边界框列表


@app.post("/api/videos/{video_id}/watermarks")
async def mark_video_watermarks(
    video_id: str,
    request: WatermarkMarkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    标记视频的水印区域
    
    参数:
        video_id: 视频ID
        request: 包含边界框数据的请求体
        db: 数据库会话
        
    返回:
        dict: 标记结果
    """
    try:
        from .watermark_detection import mark_watermark_regions
        
        # 获取视频信息
        video = await crud.get_video_by_id(db, video_id)
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"视频 {video_id} 不存在"
            )
        
        # 标记水印区域
        regions = await mark_watermark_regions(
            db=db,
            video_id=video_id,
            video_path=video.storage_path,
            bounding_boxes=request.bounding_boxes
        )
        
        await db.commit()
        
        # 转换为响应格式
        regions_data = []
        for region in regions:
            regions_data.append({
                "region_id": region.region_id,
                "video_id": region.video_id,
                "bbox": {
                    "x": region.bbox_x,
                    "y": region.bbox_y,
                    "width": region.bbox_width,
                    "height": region.bbox_height
                },
                "start_time": region.start_time,
                "end_time": region.end_time,
                "confidence": region.confidence,
                "watermark_type": region.watermark_type,
                "detection_method": region.detection_method,
                "created_at": region.created_at.isoformat() if region.created_at else None
            })
        
        return {
            "success": True,
            "data": {
                "video_id": video_id,
                "regions": regions_data,
                "count": len(regions_data)
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记水印区域失败: {str(e)}"
        )


@app.get("/api/videos/{video_id}/watermarks")
async def get_video_watermarks(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频的所有水印区域
    
    参数:
        video_id: 视频ID
        db: 数据库会话
        
    返回:
        dict: 水印区域列表
    """
    try:
        # 验证视频是否存在
        video = await crud.get_video_by_id(db, video_id)
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"视频 {video_id} 不存在"
            )
        
        # 获取水印区域
        regions = await crud.get_watermark_regions_by_video(db, video_id)
        
        # 转换为响应格式
        regions_data = []
        for region in regions:
            regions_data.append({
                "region_id": region.region_id,
                "video_id": region.video_id,
                "bbox": {
                    "x": region.bbox_x,
                    "y": region.bbox_y,
                    "width": region.bbox_width,
                    "height": region.bbox_height
                },
                "start_time": region.start_time,
                "end_time": region.end_time,
                "confidence": region.confidence,
                "watermark_type": region.watermark_type,
                "detection_method": region.detection_method,
                "created_at": region.created_at.isoformat() if region.created_at else None
            })
        
        return {
            "success": True,
            "data": {
                "video_id": video_id,
                "regions": regions_data,
                "count": len(regions_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取水印区域失败: {str(e)}"
        )


# 定义水印更新请求模型
class WatermarkUpdateRequest(BaseModel):
    bbox: Optional[dict] = None  # 新的边界框
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    watermark_type: Optional[str] = None


@app.put("/api/videos/{video_id}/watermarks/{region_id}")
async def update_video_watermark(
    video_id: str,
    region_id: str,
    request: WatermarkUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    更新水印区域
    
    参数:
        video_id: 视频ID
        region_id: 水印区域ID
        request: 包含更新数据的请求体
        db: 数据库会话
        
    返回:
        dict: 更新后的水印区域
    """
    try:
        # 验证视频是否存在
        video = await crud.get_video_by_id(db, video_id)
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"视频 {video_id} 不存在"
            )
        
        # 获取水印区域
        region = await crud.get_watermark_region_by_id(db, region_id)
        
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"水印区域 {region_id} 不存在"
            )
        
        # 验证区域是否属于该视频
        if region.video_id != video_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"水印区域 {region_id} 不属于视频 {video_id}"
            )
        
        # 准备更新数据
        update_data = {}
        
        if request.bbox is not None:
            # 验证边界框
            from .watermark_detection import validate_bounding_box
            from .models import BoundingBox
            
            bbox = BoundingBox(
                x=request.bbox.get("x", region.bbox_x),
                y=request.bbox.get("y", region.bbox_y),
                width=request.bbox.get("width", region.bbox_width),
                height=request.bbox.get("height", region.bbox_height)
            )
            
            if not await validate_bounding_box(bbox, video.resolution_width, video.resolution_height):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的边界框坐标"
                )
            
            update_data["bbox_x"] = bbox.x
            update_data["bbox_y"] = bbox.y
            update_data["bbox_width"] = bbox.width
            update_data["bbox_height"] = bbox.height
        
        if request.start_time is not None:
            if request.start_time < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="开始时间不能为负数"
                )
            update_data["start_time"] = request.start_time
        
        if request.end_time is not None:
            if request.end_time <= (request.start_time if request.start_time is not None else region.start_time):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="结束时间必须大于开始时间"
                )
            update_data["end_time"] = request.end_time
        
        if request.watermark_type is not None:
            valid_types = ["corner", "rolling", "logo", "subtitle", "manual"]
            if request.watermark_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的水印类型，必须是以下之一: {', '.join(valid_types)}"
                )
            update_data["watermark_type"] = request.watermark_type
        
        # 更新水印区域
        updated_region = await crud.update_watermark_region(db, region_id, **update_data)
        await db.commit()
        
        return {
            "success": True,
            "data": {
                "region_id": updated_region.region_id,
                "video_id": updated_region.video_id,
                "bbox": {
                    "x": updated_region.bbox_x,
                    "y": updated_region.bbox_y,
                    "width": updated_region.bbox_width,
                    "height": updated_region.bbox_height
                },
                "start_time": updated_region.start_time,
                "end_time": updated_region.end_time,
                "confidence": updated_region.confidence,
                "watermark_type": updated_region.watermark_type,
                "detection_method": updated_region.detection_method,
                "created_at": updated_region.created_at.isoformat() if updated_region.created_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新水印区域失败: {str(e)}"
        )


@app.delete("/api/videos/{video_id}/watermarks/{region_id}")
async def delete_video_watermark(
    video_id: str,
    region_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除水印区域
    
    参数:
        video_id: 视频ID
        region_id: 水印区域ID
        db: 数据库会话
        
    返回:
        dict: 删除结果
    """
    try:
        # 验证视频是否存在
        video = await crud.get_video_by_id(db, video_id)
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"视频 {video_id} 不存在"
            )
        
        # 获取水印区域
        region = await crud.get_watermark_region_by_id(db, region_id)
        
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"水印区域 {region_id} 不存在"
            )
        
        # 验证区域是否属于该视频
        if region.video_id != video_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"水印区域 {region_id} 不属于视频 {video_id}"
            )
        
        # 删除水印区域
        success = await crud.delete_watermark_region(db, region_id)
        await db.commit()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除水印区域失败"
            )
        
        return {
            "success": True,
            "data": {
                "video_id": video_id,
                "region_id": region_id,
                "message": "水印区域已成功删除"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除水印区域失败: {str(e)}"
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
# 定义单个视频去除请求模型
class SingleRemovalRequest(BaseModel):
    regions: TypingList[dict]  # 水印区域列表
    mode: str = "crop_reconstruct"  # 处理模式：crop_reconstruct, ai_inpainting, blur_replace
    user_id: str = "default_user"
    client_id: Optional[str] = None  # 用于WebSocket进度推送


@app.post("/api/videos/{video_id}/remove")
async def remove_single_video(
    video_id: str,
    request: SingleRemovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    执行单个视频水印去除

    参数:
        video_id: 视频ID
        request: 包含水印区域和处理参数的请求体
        db: 数据库会话

    返回:
        dict: 任务信息，包含task_id用于状态跟踪
    """
    try:
        # 获取视频信息
        video = await crud.get_video_by_id(db, video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"视频 {video_id} 不存在"
            )

        # 验证处理模式
        valid_modes = ["crop_reconstruct", "ai_inpainting", "blur_replace"]
        if request.mode not in valid_modes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的处理模式，必须是以下之一: {', '.join(valid_modes)}"
            )

        # 创建处理任务记录
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        await crud.create_processing_task(
            db=db,
            task_id=task_id,
            user_id=request.user_id,
            video_id=video_id,
            task_type="removal",
            status="pending",
            parameters={
                "mode": request.mode,
                "regions": request.regions
            }
        )

        await db.commit()

        # 准备视频元数据
        video_metadata = {
            "resolution_width": video.resolution_width,
            "resolution_height": video.resolution_height,
            "duration": video.duration,
            "codec": video.codec,
            "framerate": video.framerate
        }

        # 如果提供了client_id，使用WebSocket推送进度
        websocket_callback = manager.send_message if request.client_id else None

        # 异步执行处理（不等待完成）
        import asyncio
        asyncio.create_task(
            task_processor.process_removal_task(
                db=db,
                task_id=task_id,
                video_id=video_id,
                video_path=video.storage_path,
                regions=request.regions,
                video_metadata=video_metadata,
                websocket_callback=websocket_callback,
                client_id=request.client_id
            )
        )

        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "video_id": video_id,
                "status": "pending",
                "message": "水印去除任务已创建，正在处理中"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建水印去除任务失败: {str(e)}"
        )


@app.post("/api/batch/remove")


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
@app.get("/api/tasks/{task_id}")
async def get_task_status_endpoint(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务状态

    参数:
        task_id: 任务ID
        db: 数据库会话

    返回:
        dict: 任务详细信息，包括状态、进度、结果等
    """
    try:
        # 获取任务信息
        task = await crud.get_task_by_id(db, task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在"
            )

        # 获取视频信息
        video = await crud.get_video_by_id(db, task.video_id)

        # 构建响应数据
        response_data = {
            "task_id": task.task_id,
            "user_id": task.user_id,
            "video_id": task.video_id,
            "task_type": task.task_type,
            "status": task.status,
            "parameters": task.parameters,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "result": task.result
        }

        # 添加视频信息
        if video:
            response_data["video"] = {
                "video_id": video.video_id,
                "format": video.format,
                "resolution": {
                    "width": video.resolution_width,
                    "height": video.resolution_height
                },
                "duration": video.duration,
                "storage_path": video.storage_path
            }

        # 如果任务已完成且有输出路径，添加输出文件信息
        if task.status == "completed" and task.result and "output_path" in task.result:
            output_path = Path(task.result["output_path"])
            if output_path.exists():
                response_data["output_file"] = {
                    "path": task.result["output_path"],
                    "size": output_path.stat().st_size,
                    "exists": True
                }

        return {
            "success": True,
            "data": response_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}"
        )


@app.get("/api/batch/{job_id}")


@app.get("/api/videos")
async def get_videos(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频列表（支持分页）
    
    参数:
        page: 页码（从1开始）
        page_size: 每页数量（默认20）
        user_id: 用户ID（可选，如果提供则只返回该用户的视频）
        db: 数据库会话
        
    返回:
        dict: 包含视频列表和分页信息
    """
    try:
        # 验证分页参数
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="页码必须大于等于1"
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="每页数量必须在1-100之间"
            )
        
        # 计算偏移量
        skip = (page - 1) * page_size
        
        # 获取视频列表
        if user_id:
            videos = await crud.get_videos_by_user(db, user_id, skip=skip, limit=page_size)
            total_count = await crud.get_videos_count_by_user(db, user_id)
        else:
            videos = await crud.get_all_videos(db, skip=skip, limit=page_size)
            # 获取总数
            from sqlalchemy import select, func
            from .database import Video as DBVideo
            result = await db.execute(select(func.count(DBVideo.video_id)))
            total_count = result.scalar_one()
        
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size
        
        # 构建响应数据
        video_list = []
        for video in videos:
            video_list.append({
                "video_id": video.video_id,
                "user_id": video.user_id,
                "format": video.format,
                "resolution": {
                    "width": video.resolution_width,
                    "height": video.resolution_height
                },
                "duration": video.duration,
                "codec": video.codec,
                "framerate": video.framerate,
                "bitrate": video.bitrate,
                "file_size": video.file_size,
                "storage_path": video.storage_path,
                "import_source": video.import_source,
                "created_at": video.created_at.isoformat() if video.created_at else None
            })
        
        return {
            "success": True,
            "data": {
                "videos": video_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取视频列表失败: {str(e)}"
        )


@app.get("/api/tasks")
async def get_tasks_list(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
    task_status: Optional[str] = None,
    task_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务列表（支持分页和过滤）

    参数:
        page: 页码（从1开始）
        page_size: 每页数量（默认20）
        user_id: 用户ID（可选，过滤特定用户的任务）
        task_status: 任务状态（可选，过滤特定状态的任务）
        task_type: 任务类型（可选，过滤特定类型的任务）
        db: 数据库会话

    返回:
        dict: 包含任务列表和分页信息
    """
    try:
        # 验证分页参数
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="页码必须大于等于1"
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="每页数量必须在1-100之间"
            )

        # 验证状态参数
        if task_status:
            valid_statuses = ["pending", "processing", "completed", "failed"]
            if task_status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的状态，必须是以下之一: {', '.join(valid_statuses)}"
                )

        # 验证任务类型参数
        if task_type:
            valid_types = ["detection", "removal", "optimization"]
            if task_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的任务类型，必须是以下之一: {', '.join(valid_types)}"
                )

        # 计算偏移量
        skip = (page - 1) * page_size

        # 构建查询
        from sqlalchemy import select, func, and_
        from .database import ProcessingTask as DBProcessingTask

        # 构建过滤条件
        filters = []
        if user_id:
            filters.append(DBProcessingTask.user_id == user_id)
        if task_status:
            filters.append(DBProcessingTask.status == task_status)
        if task_type:
            filters.append(DBProcessingTask.task_type == task_type)

        # 查询任务列表
        stmt = select(DBProcessingTask)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(DBProcessingTask.created_at.desc()).offset(skip).limit(page_size)

        result = await db.execute(stmt)
        tasks = result.scalars().all()

        # 查询总数
        count_stmt = select(func.count(DBProcessingTask.task_id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar_one()

        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size

        # 构建任务列表
        task_list = []
        for task in tasks:
            task_data = {
                "task_id": task.task_id,
                "user_id": task.user_id,
                "video_id": task.video_id,
                "task_type": task.task_type,
                "status": task.status,
                "parameters": task.parameters,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error_message": task.error_message,
                "result": task.result
            }
            task_list.append(task_data)

        return {
            "success": True,
            "data": {
                "tasks": task_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                },
                "filters": {
                    "user_id": user_id,
                    "status": task_status,
                    "task_type": task_type
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@app.get("/api/videos")


@app.get("/api/videos/{video_id}")
async def get_video_details(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频详情（包括水印区域和处理任务）
    
    参数:
        video_id: 视频ID
        db: 数据库会话
        
    返回:
        dict: 视频详细信息
    """
    try:
        # 获取视频及其关联数据
        video = await crud.get_video_with_relations(db, video_id)
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"视频 {video_id} 不存在"
            )
        
        # 构建水印区域列表
        watermark_regions = []
        for region in video.watermark_regions:
            watermark_regions.append({
                "region_id": region.region_id,
                "bbox": {
                    "x": region.bbox_x,
                    "y": region.bbox_y,
                    "width": region.bbox_width,
                    "height": region.bbox_height
                },
                "start_time": region.start_time,
                "end_time": region.end_time,
                "confidence": region.confidence,
                "watermark_type": region.watermark_type,
                "detection_method": region.detection_method,
                "created_at": region.created_at.isoformat() if region.created_at else None
            })
        
        # 构建处理任务列表
        processing_tasks = []
        for task in video.processing_tasks:
            processing_tasks.append({
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status,
                "parameters": task.parameters,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error_message": task.error_message,
                "result": task.result
            })
        
        # 构建响应数据
        return {
            "success": True,
            "data": {
                "video_id": video.video_id,
                "user_id": video.user_id,
                "format": video.format,
                "resolution": {
                    "width": video.resolution_width,
                    "height": video.resolution_height
                },
                "duration": video.duration,
                "codec": video.codec,
                "framerate": video.framerate,
                "bitrate": video.bitrate,
                "file_size": video.file_size,
                "storage_path": video.storage_path,
                "import_source": video.import_source,
                "created_at": video.created_at.isoformat() if video.created_at else None,
                "watermark_regions": watermark_regions,
                "processing_tasks": processing_tasks
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取视频详情失败: {str(e)}"
        )


@app.delete("/api/videos/{video_id}")
async def delete_video_endpoint(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除视频及其关联文件
    
    参数:
        video_id: 视频ID
        db: 数据库会话
        
    返回:
        dict: 删除结果
    """
    try:
        # 获取视频信息
        video = await crud.get_video_by_id(db, video_id)
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"视频 {video_id} 不存在"
            )
        
        # 删除物理文件
        deleted_files = []
        
        # 1. 删除原始视频文件
        video_path = Path(video.storage_path)
        if video_path.exists():
            try:
                video_path.unlink()
                deleted_files.append(str(video_path))
            except Exception as e:
                print(f"删除视频文件失败: {e}")
        
        # 2. 删除缩略图文件
        thumbnail_path = THUMBNAIL_DIR / f"{video_id}_*.jpg"
        import glob
        for thumb_file in glob.glob(str(thumbnail_path)):
            try:
                Path(thumb_file).unlink()
                deleted_files.append(thumb_file)
            except Exception as e:
                print(f"删除缩略图失败: {e}")
        
        # 3. 删除输出文件（查找所有相关的处理任务）
        tasks = await crud.get_tasks_by_video(db, video_id)
        for task in tasks:
            if task.result and "output_path" in task.result:
                output_path = Path(task.result["output_path"])
                if output_path.exists():
                    try:
                        output_path.unlink()
                        deleted_files.append(str(output_path))
                    except Exception as e:
                        print(f"删除输出文件失败: {e}")
        
        # 删除数据库记录（级联删除水印区域和任务）
        success = await crud.delete_video(db, video_id)
        await db.commit()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除数据库记录失败"
            )
        
        return {
            "success": True,
            "data": {
                "video_id": video_id,
                "message": "视频及其关联文件已成功删除",
                "deleted_files": deleted_files
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除视频失败: {str(e)}"
        )


@app.get("/api/videos/{video_id}/output")
async def download_output_video(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    下载处理后的视频
    
    参数:
        video_id: 原始视频ID或输出视频ID
        db: 数据库会话
        
    返回:
        FileResponse: 视频文件
    """
    from fastapi.responses import FileResponse
    from sqlalchemy import select, or_
    from .database import ProcessingTask as DBProcessingTask
    
    try:
        # 查询该视频的已完成处理任务（按完成时间降序，获取最新的）
        stmt = select(DBProcessingTask).where(
            DBProcessingTask.video_id == video_id,
            DBProcessingTask.status == "completed",
            DBProcessingTask.result.isnot(None)
        ).order_by(DBProcessingTask.completed_at.desc())
        
        result = await db.execute(stmt)
        task = result.scalars().first()  # 使用 first() 而不是 scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到视频 {video_id} 的处理结果"
            )
        
        # 从任务结果中获取输出路径
        output_path = task.result.get("output_path")
        if not output_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="处理结果中未找到输出路径"
            )
        
        # 验证文件是否存在
        output_file = Path(output_path)
        if not output_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"输出文件不存在: {output_path}"
            )
        
        # 获取输出视频ID和文件名
        output_video_id = task.result.get("output_video_id", "output")
        filename = f"{output_video_id}.mp4"
        
        # 返回文件响应
        return FileResponse(
            path=str(output_file),
            media_type="video/mp4",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载输出视频失败: {str(e)}"
        )
