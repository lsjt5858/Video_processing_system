"""
视频导入模块

实现本地视频上传、URL下载和批量上传功能
"""

import os
import uuid
import shutil
import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from .models import VideoFormat, VideoMetadata, VideoImportResult
from .database import get_db
from .crud import create_video


# 支持的视频格式
SUPPORTED_FORMATS = {".mp4", ".avi", ".mov", ".mkv"}

# 文件大小限制（5GB）
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB in bytes

# 批量上传限制
MAX_BATCH_SIZE = 50

# 获取上传目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"


class FileSizeExceededError(Exception):
    """文件大小超过限制错误"""
    pass


class UnsupportedFormatError(Exception):
    """不支持的视频格式错误"""
    pass


class MetadataExtractionError(Exception):
    """元数据提取失败错误"""
    pass


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
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(
            f"不支持的视频格式: {file_ext}。支持的格式: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    return file_ext.lstrip('.')


def validate_file_size(file_size: int) -> None:
    """
    验证文件大小
    
    参数:
        file_size: 文件大小（字节）
        
    异常:
        FileSizeExceededError: 文件大小超过限制
    """
    if file_size > MAX_FILE_SIZE:
        size_gb = file_size / (1024 * 1024 * 1024)
        raise FileSizeExceededError(
            f"文件大小 {size_gb:.2f}GB 超过限制 5GB"
        )


def extract_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    使用FFprobe提取视频元数据
    
    参数:
        video_path: 视频文件路径
        
    返回:
        Dict[str, Any]: 包含视频元数据的字典
        
    异常:
        MetadataExtractionError: 元数据提取失败
    """
    try:
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
            raise MetadataExtractionError(
                f"FFprobe执行失败: {result.stderr}"
            )
        
        # 解析JSON输出
        probe_data = json.loads(result.stdout)
        
        # 查找视频流
        video_stream = None
        for stream in probe_data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise MetadataExtractionError("未找到视频流")
        
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
            raise MetadataExtractionError("无法提取视频分辨率")
        if duration == 0:
            raise MetadataExtractionError("无法提取视频时长")
        if framerate == 0:
            raise MetadataExtractionError("无法提取视频帧率")
        
        return {
            'resolution': (width, height),
            'duration': duration,
            'codec': codec,
            'framerate': framerate,
            'bitrate': bitrate,
            'file_size': file_size
        }
        
    except subprocess.TimeoutExpired:
        raise MetadataExtractionError("元数据提取超时")
    except json.JSONDecodeError as e:
        raise MetadataExtractionError(f"解析FFprobe输出失败: {str(e)}")
    except Exception as e:
        raise MetadataExtractionError(f"元数据提取失败: {str(e)}")


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
    user_id: str = "default_user"
) -> dict:
    """
    批量上传视频文件
    
    参数:
        files: 文件列表（最多50个）
        user_id: 用户ID
        
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
        "failed": []
    }
    
    # 处理每个文件
    for file in files:
        try:
            result = await upload_single_video(file, user_id)
            results["successful"].append({
                "filename": file.filename,
                "video_id": result.video_id,
                "file_size": result.metadata.file_size,
                "storage_path": result.storage_path
            })
        except (FileSizeExceededError, UnsupportedFormatError, MetadataExtractionError) as e:
            results["failed"].append({
                "filename": file.filename,
                "error": str(e)
            })
        except Exception as e:
            results["failed"].append({
                "filename": file.filename,
                "error": f"上传失败: {str(e)}"
            })
    
    results["success_count"] = len(results["successful"])
    results["failed_count"] = len(results["failed"])
    
    return results
