"""
视频导入模块

实现本地视频上传、URL下载和批量上传功能
"""

import os
import uuid
import shutil
import json
import subprocess
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

from fastapi import UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
import yt_dlp

from .models import VideoFormat, VideoMetadata, VideoImportResult
from .database import get_db
from .crud import create_video


from .errors import (
    FileSizeExceededError,
    UnsupportedFormatError,
    MetadataExtractionError,
    InvalidUrlError,
    VideoNotAccessibleError,
    CorruptedVideoError,
    FFmpegError,
    log_error
)

# 支持的视频格式
SUPPORTED_FORMATS = {".mp4", ".avi", ".mov", ".mkv"}
SUPPORTED_FORMATS_LIST = ["mp4", "avi", "mov", "mkv"]

# 文件大小限制（5GB）
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB in bytes

# 批量上传限制
MAX_BATCH_SIZE = 50

# 获取上传目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"


def validate_url(url: str) -> None:
    """
    验证URL有效性
    
    参数:
        url: 视频链接
        
    异常:
        InvalidUrlError: URL无效
    """
    if not url or not url.strip():
        raise InvalidUrlError("", "URL不能为空")
    
    url = url.strip()
    
    # 基本URL格式验证
    if not url.startswith(('http://', 'https://')):
        raise InvalidUrlError(url, "URL必须以http://或https://开头")
    
    # 检查URL长度
    if len(url) > 2048:
        raise InvalidUrlError(url, "URL长度超过限制（2048字符）")
    
    # 检查是否包含空格
    if ' ' in url:
        raise InvalidUrlError(url, "URL不能包含空格")
    
    # 简单的域名验证
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.netloc:
            raise InvalidUrlError(url, "URL格式无效：缺少域名")
    except Exception as e:
        raise InvalidUrlError(url, f"URL解析失败: {str(e)}")


def validate_video_format(filename: str) -> str:
    """
    验证视频格式
    
    参数:
        filename: 文件名
        
    返回:
        str: 文件扩展名（小写，不含点）
        
    异常:
        UnsupportedFormatError: 不支持的格式
    """
    if not filename:
        raise UnsupportedFormatError("", SUPPORTED_FORMATS_LIST)
    
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(file_ext, SUPPORTED_FORMATS_LIST)
    
    return file_ext.lstrip('.')


def validate_file_size(file_size: int, filename: str = "") -> None:
    """
    验证文件大小
    
    参数:
        file_size: 文件大小（字节）
        filename: 文件名（可选）
        
    异常:
        FileSizeExceededError: 文件大小超过限制
    """
    if file_size > MAX_FILE_SIZE:
        raise FileSizeExceededError(file_size, MAX_FILE_SIZE, filename)


def extract_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    使用FFprobe提取视频元数据
    
    参数:
        video_path: 视频文件路径
        
    返回:
        Dict[str, Any]: 包含视频元数据的字典
        
    异常:
        MetadataExtractionError: 元数据提取失败
        CorruptedVideoError: 视频文件损坏
    """
    try:
        # 验证文件存在
        if not Path(video_path).exists():
            raise MetadataExtractionError(video_path, "文件不存在")
        
        # 验证文件大小
        file_size = Path(video_path).stat().st_size
        if file_size == 0:
            raise CorruptedVideoError(video_path, "文件大小为0")
        
        # 使用ffprobe提取视频信息
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30秒超时
        )
        
        if result.returncode != 0:
            stderr = result.stderr or "未知错误"
            if "Invalid data found" in stderr or "moov atom not found" in stderr:
                raise CorruptedVideoError(video_path, stderr)
            raise MetadataExtractionError(video_path, f"FFprobe执行失败: {stderr}")
        
        # 解析JSON输出
        try:
            probe_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise MetadataExtractionError(video_path, f"解析FFprobe输出失败: {str(e)}")
        
        # 查找视频流
        video_stream = None
        for stream in probe_data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise CorruptedVideoError(video_path, "未找到视频流")
        
        # 提取元数据
        format_info = probe_data.get('format', {})
        
        # 分辨率
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        
        # 时长（秒）
        duration = float(format_info.get('duration', 0))
        if duration == 0:
            # 尝试从视频流获取时长
            duration = float(video_stream.get('duration', 0))
        
        # 编码格式
        codec = video_stream.get('codec_name', 'unknown')
        
        # 帧率
        fps_str = video_stream.get('r_frame_rate', '0/1')
        try:
            num, den = map(int, fps_str.split('/'))
            framerate = num / den if den != 0 else 0.0
        except (ValueError, ZeroDivisionError):
            framerate = 0.0
        
        # 码率（bps）
        bitrate = int(format_info.get('bit_rate', 0))
        if bitrate == 0:
            # 尝试从视频流获取码率
            bitrate = int(video_stream.get('bit_rate', 0))
        
        # 文件大小
        file_size = int(format_info.get('size', 0))
        if file_size == 0:
            # 如果format中没有size，从文件系统获取
            file_size = Path(video_path).stat().st_size
        
        # 验证必需字段
        if width == 0 or height == 0:
            raise CorruptedVideoError(video_path, "无法提取视频分辨率")
        if duration == 0:
            raise CorruptedVideoError(video_path, "无法提取视频时长")
        if framerate == 0:
            raise MetadataExtractionError(video_path, "无法提取视频帧率")
        
        return {
            'resolution': (width, height),
            'duration': duration,
            'codec': codec,
            'framerate': framerate,
            'bitrate': bitrate,
            'file_size': file_size
        }
        
    except subprocess.TimeoutExpired:
        raise MetadataExtractionError(video_path, "元数据提取超时（30秒）")
    except (CorruptedVideoError, MetadataExtractionError):
        # 重新抛出已知错误
        raise
    except Exception as e:
        log_error(e, {"video_path": video_path, "operation": "extract_metadata"})
        raise MetadataExtractionError(video_path, str(e))


async def save_upload_file(upload_file: UploadFile) -> tuple[str, int]:
    """
    保存上传的文件到uploads目录
    
    参数:
        upload_file: FastAPI UploadFile对象
        
    返回:
        tuple[str, int]: (保存的文件路径, 文件大小)
        
    异常:
        FileSizeExceededError: 文件大小超过限制
        UnsupportedFormatError: 不支持的格式
    """
    # 验证格式
    file_format = validate_video_format(upload_file.filename)
    
    # 生成唯一文件名
    video_id = str(uuid.uuid4())
    filename = f"{video_id}.{file_format}"
    file_path = UPLOAD_DIR / filename
    
    # 保存文件并计算大小
    file_size = 0
    try:
        with open(file_path, "wb") as buffer:
            while chunk := await upload_file.read(8192):  # 8KB chunks
                file_size += len(chunk)
                
                # 检查文件大小
                if file_size > MAX_FILE_SIZE:
                    # 删除部分上传的文件
                    buffer.close()
                    if file_path.exists():
                        file_path.unlink()
                    raise FileSizeExceededError(
                        f"文件大小超过限制 5GB"
                    )
                
                buffer.write(chunk)
    except Exception as e:
        # 清理失败的上传
        if file_path.exists():
            file_path.unlink()
        raise e
    
    return str(file_path), file_size


async def upload_single_video(
    file: UploadFile,
    user_id: str = "default_user"
) -> VideoImportResult:
    """
    上传单个视频文件
    
    参数:
        file: 上传的文件对象
        user_id: 用户ID
        
    返回:
        VideoImportResult: 导入结果
        
    异常:
        FileSizeExceededError: 文件大小超过5GB
        UnsupportedFormatError: 不支持的视频格式
        MetadataExtractionError: 元数据提取失败
    """
    # 保存文件
    file_path, file_size = await save_upload_file(file)
    
    # 生成视频ID（从文件名提取）
    video_id = Path(file_path).stem
    
    # 获取文件格式
    file_format = Path(file_path).suffix.lstrip('.').lower()
    
    try:
        # 提取视频元数据
        metadata_dict = extract_video_metadata(file_path)
        
        # 创建元数据对象
        metadata = VideoMetadata(
            video_id=video_id,
            format=VideoFormat(file_format),
            resolution=metadata_dict['resolution'],
            duration=metadata_dict['duration'],
            codec=metadata_dict['codec'],
            framerate=metadata_dict['framerate'],
            bitrate=metadata_dict['bitrate'],
            file_size=metadata_dict['file_size'],
            created_at=datetime.now()
        )
        
        # 保存到数据库
        db_gen = get_db()
        db = await anext(db_gen)
        try:
            await create_video(
                db=db,
                video_id=video_id,
                user_id=user_id,
                format=file_format,
                resolution_width=metadata.resolution[0],
                resolution_height=metadata.resolution[1],
                duration=metadata.duration,
                codec=metadata.codec,
                framerate=metadata.framerate,
                bitrate=metadata.bitrate,
                file_size=metadata.file_size,
                storage_path=file_path,
                import_source="local"
            )
        finally:
            await db.close()
        
        # 返回导入结果
        return VideoImportResult(
            video_id=video_id,
            metadata=metadata,
            storage_path=file_path,
            import_source="local",
            import_time=datetime.now()
        )
        
    except MetadataExtractionError as e:
        # 元数据提取失败，删除已上传的文件
        if Path(file_path).exists():
            Path(file_path).unlink()
        raise e


async def upload_batch_videos(
    files: List[UploadFile],
    user_id: str = "default_user",
    websocket_callback: Optional[Callable] = None,
    client_id: Optional[str] = None
) -> dict:
    """
    批量上传视频文件（支持并发和进度推送）
    
    参数:
        files: 文件列表（最多50个）
        user_id: 用户ID
        websocket_callback: WebSocket回调函数，用于推送进度
        client_id: 客户端ID，用于WebSocket消息推送
        
    返回:
        dict: 批量上传结果，包含成功和失败的文件信息
        
    异常:
        HTTPException: 文件数量超过限制
    """
    # 验证文件数量
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批量上传最多支持 {MAX_BATCH_SIZE} 个文件，当前: {len(files)}"
        )
    
    results = {
        "total": len(files),
        "successful": [],
        "failed": [],
        "in_progress": []
    }
    
    # 创建信号量，限制并发上传数量为5
    semaphore = asyncio.Semaphore(5)
    
    # 用于跟踪进度的共享状态
    completed_count = 0
    lock = asyncio.Lock()
    
    async def upload_with_progress(file: UploadFile, index: int):
        """带进度跟踪的上传函数"""
        nonlocal completed_count
        
        async with semaphore:
            try:
                # 推送开始上传消息
                if websocket_callback and client_id:
                    await websocket_callback(client_id, {
                        "type": "batch_upload_progress",
                        "file_index": index,
                        "filename": file.filename,
                        "status": "uploading",
                        "progress": 0,
                        "completed": completed_count,
                        "total": len(files)
                    })
                
                # 执行上传
                result = await upload_single_video(file, user_id)
                
                # 更新成功结果
                async with lock:
                    completed_count += 1
                    results["successful"].append({
                        "filename": file.filename,
                        "video_id": result.video_id,
                        "file_size": result.metadata.file_size,
                        "storage_path": result.storage_path,
                        "index": index
                    })
                
                # 推送完成消息
                if websocket_callback and client_id:
                    await websocket_callback(client_id, {
                        "type": "batch_upload_progress",
                        "file_index": index,
                        "filename": file.filename,
                        "status": "completed",
                        "progress": 100,
                        "video_id": result.video_id,
                        "completed": completed_count,
                        "total": len(files)
                    })
                    
            except (FileSizeExceededError, UnsupportedFormatError, MetadataExtractionError) as e:
                # 更新失败结果
                async with lock:
                    completed_count += 1
                    results["failed"].append({
                        "filename": file.filename,
                        "error": str(e),
                        "index": index
                    })
                
                # 推送失败消息
                if websocket_callback and client_id:
                    await websocket_callback(client_id, {
                        "type": "batch_upload_progress",
                        "file_index": index,
                        "filename": file.filename,
                        "status": "failed",
                        "error": str(e),
                        "completed": completed_count,
                        "total": len(files)
                    })
                    
            except Exception as e:
                # 更新失败结果
                async with lock:
                    completed_count += 1
                    results["failed"].append({
                        "filename": file.filename,
                        "error": f"上传失败: {str(e)}",
                        "index": index
                    })
                
                # 推送失败消息
                if websocket_callback and client_id:
                    await websocket_callback(client_id, {
                        "type": "batch_upload_progress",
                        "file_index": index,
                        "filename": file.filename,
                        "status": "failed",
                        "error": f"上传失败: {str(e)}",
                        "completed": completed_count,
                        "total": len(files)
                    })
    
    # 创建所有上传任务
    tasks = [upload_with_progress(file, i) for i, file in enumerate(files)]
    
    # 并发执行所有任务
    await asyncio.gather(*tasks)
    
    results["success_count"] = len(results["successful"])
    results["failed_count"] = len(results["failed"])
    
    # 推送批量上传完成消息
    if websocket_callback and client_id:
        await websocket_callback(client_id, {
            "type": "batch_upload_complete",
            "total": len(files),
            "success_count": results["success_count"],
            "failed_count": results["failed_count"]
        })
    
    return results



class DownloadProgressHook:
    """
    yt-dlp下载进度回调类
    
    用于捕获下载进度并通过WebSocket推送给客户端
    """
    def __init__(self, websocket_callback: Optional[Callable] = None, client_id: Optional[str] = None):
        self.websocket_callback = websocket_callback
        self.client_id = client_id
        self.last_progress = 0
    
    def __call__(self, d: dict):
        """
        yt-dlp进度回调函数
        
        参数:
            d: 包含下载状态信息的字典
        """
        if d['status'] == 'downloading':
            # 提取进度信息
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                progress = int((downloaded / total) * 100)
                
                # 只在进度变化时推送（避免过于频繁）
                if progress != self.last_progress:
                    self.last_progress = progress
                    
                    # 如果提供了WebSocket回调，推送进度
                    if self.websocket_callback and self.client_id:
                        try:
                            # 尝试在当前事件循环中创建任务
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.create_task(
                                    self.websocket_callback(self.client_id, {
                                        "type": "download_progress",
                                        "progress": progress,
                                        "downloaded_bytes": downloaded,
                                        "total_bytes": total,
                                        "speed": d.get('speed', 0),
                                        "eta": d.get('eta', 0)
                                    })
                                )
                        except RuntimeError:
                            # 如果没有运行的事件循环，忽略WebSocket推送
                            pass
        
        elif d['status'] == 'finished':
            # 下载完成
            if self.websocket_callback and self.client_id:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            self.websocket_callback(self.client_id, {
                                "type": "download_complete",
                                "message": "视频下载完成，正在处理..."
                            })
                        )
                except RuntimeError:
                    pass


async def download_video_from_url(
    url: str,
    user_id: str = "default_user",
    websocket_callback: Optional[Callable] = None,
    client_id: Optional[str] = None
) -> VideoImportResult:
    """
    从URL下载视频
    
    参数:
        url: 视频链接
        user_id: 用户ID
        websocket_callback: WebSocket回调函数（可选）
        client_id: 客户端ID（可选）
        
    返回:
        VideoImportResult: 导入结果
        
    异常:
        InvalidUrlError: 链接无效
        VideoNotAccessibleError: 视频不可访问
        UnsupportedFormatError: 不支持的视频格式
        MetadataExtractionError: 元数据提取失败
    """
    # 验证URL
    validate_url(url)
    
    # 生成唯一视频ID
    video_id = str(uuid.uuid4())
    
    # 配置yt-dlp选项
    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # 优先下载mp4格式
        'outtmpl': str(UPLOAD_DIR / f'{video_id}.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [DownloadProgressHook(websocket_callback, client_id)],
        # 支持常见视频网站
        'extract_flat': False,
        # 超时设置
        'socket_timeout': 30,
    }
    
    try:
        # 发送开始下载通知
        if websocket_callback and client_id:
            await websocket_callback(client_id, {
                "type": "download_start",
                "message": "开始下载视频...",
                "url": url
            })
        
        # 使用yt-dlp下载视频
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 先提取视频信息（验证URL有效性）
            try:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    raise InvalidUrlError(f"无法解析视频链接: {url}")
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                if "Unsupported URL" in error_msg or "not a valid URL" in error_msg:
                    raise InvalidUrlError(f"无效的视频链接: {url}")
                elif "Video unavailable" in error_msg or "Private video" in error_msg:
                    raise VideoNotAccessibleError(f"视频不可访问: {url}")
                else:
                    raise VideoNotAccessibleError(f"下载失败: {error_msg}")
            except Exception as e:
                raise InvalidUrlError(f"链接解析失败: {str(e)}")
            
            # 下载视频
            try:
                info = ydl.extract_info(url, download=True)
            except yt_dlp.utils.DownloadError as e:
                raise VideoNotAccessibleError(f"视频下载失败: {str(e)}")
            except Exception as e:
                raise VideoNotAccessibleError(f"下载过程出错: {str(e)}")
        
        # 查找下载的文件
        downloaded_file = None
        for ext in ['mp4', 'mkv', 'webm', 'avi', 'mov']:
            potential_file = UPLOAD_DIR / f'{video_id}.{ext}'
            if potential_file.exists():
                downloaded_file = potential_file
                break
        
        if not downloaded_file or not downloaded_file.exists():
            raise VideoNotAccessibleError("下载的文件未找到")
        
        # 如果不是支持的格式，需要转换
        file_ext = downloaded_file.suffix.lower()
        if file_ext not in SUPPORTED_FORMATS:
            # 转换为mp4格式
            output_file = UPLOAD_DIR / f'{video_id}.mp4'
            
            if websocket_callback and client_id:
                await websocket_callback(client_id, {
                    "type": "converting",
                    "message": "正在转换视频格式..."
                })
            
            try:
                # 使用FFmpeg转换
                cmd = [
                    'ffmpeg',
                    '-i', str(downloaded_file),
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    '-y',  # 覆盖输出文件
                    str(output_file)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode != 0:
                    raise Exception(f"视频转换失败: {result.stderr}")
                
                # 删除原文件
                downloaded_file.unlink()
                downloaded_file = output_file
                file_ext = '.mp4'
                
            except subprocess.TimeoutExpired:
                if downloaded_file.exists():
                    downloaded_file.unlink()
                raise MetadataExtractionError("视频转换超时")
            except Exception as e:
                if downloaded_file.exists():
                    downloaded_file.unlink()
                raise MetadataExtractionError(f"视频转换失败: {str(e)}")
        
        file_path = str(downloaded_file)
        file_format = file_ext.lstrip('.')
        
        # 发送元数据提取通知
        if websocket_callback and client_id:
            await websocket_callback(client_id, {
                "type": "extracting_metadata",
                "message": "正在提取视频元数据..."
            })
        
        try:
            # 提取视频元数据
            metadata_dict = extract_video_metadata(file_path)
            
            # 创建元数据对象
            metadata = VideoMetadata(
                video_id=video_id,
                format=VideoFormat(file_format),
                resolution=metadata_dict['resolution'],
                duration=metadata_dict['duration'],
                codec=metadata_dict['codec'],
                framerate=metadata_dict['framerate'],
                bitrate=metadata_dict['bitrate'],
                file_size=metadata_dict['file_size'],
                created_at=datetime.now()
            )
            
            # 保存到数据库
            db_gen = get_db()
            db = await anext(db_gen)
            try:
                await create_video(
                    db=db,
                    video_id=video_id,
                    user_id=user_id,
                    format=file_format,
                    resolution_width=metadata.resolution[0],
                    resolution_height=metadata.resolution[1],
                    duration=metadata.duration,
                    codec=metadata.codec,
                    framerate=metadata.framerate,
                    bitrate=metadata.bitrate,
                    file_size=metadata.file_size,
                    storage_path=file_path,
                    import_source="url"
                )
            finally:
                await db.close()
            
            # 发送完成通知
            if websocket_callback and client_id:
                await websocket_callback(client_id, {
                    "type": "import_complete",
                    "message": "视频导入完成",
                    "video_id": video_id
                })
            
            # 返回导入结果
            return VideoImportResult(
                video_id=video_id,
                metadata=metadata,
                storage_path=file_path,
                import_source="url",
                import_time=datetime.now()
            )
            
        except MetadataExtractionError as e:
            # 元数据提取失败，删除已下载的文件
            if Path(file_path).exists():
                Path(file_path).unlink()
            raise e
        
    except (InvalidUrlError, VideoNotAccessibleError, UnsupportedFormatError, MetadataExtractionError):
        # 重新抛出已知错误
        raise
    except Exception as e:
        # 捕获其他未预期的错误
        # 清理可能下载的文件
        for ext in ['mp4', 'mkv', 'webm', 'avi', 'mov']:
            potential_file = UPLOAD_DIR / f'{video_id}.{ext}'
            if potential_file.exists():
                potential_file.unlink()
        
        raise VideoNotAccessibleError(f"下载过程出错: {str(e)}")
