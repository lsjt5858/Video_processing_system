"""
错误处理模块

定义自定义异常类和错误响应格式
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """视频处理基础错误类"""
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "timestamp": datetime.now().isoformat()
            }
        }


# 输入验证错误
class FileSizeExceededError(VideoProcessingError):
    """文件大小超过限制错误"""
    def __init__(self, file_size: int, max_size: int, filename: str = ""):
        size_gb = file_size / (1024 * 1024 * 1024)
        max_gb = max_size / (1024 * 1024 * 1024)
        super().__init__(
            message=f"文件大小 {size_gb:.2f}GB 超过限制 {max_gb:.1f}GB",
            error_code="FILE_SIZE_EXCEEDED",
            details={
                "file_size": file_size,
                "max_size": max_size,
                "file_name": filename
            },
            status_code=413
        )


class UnsupportedFormatError(VideoProcessingError):
    """不支持的视频格式错误"""
    def __init__(self, format: str, supported_formats: list):
        super().__init__(
            message=f"不支持的视频格式: {format}",
            error_code="UNSUPPORTED_FORMAT",
            details={
                "format": format,
                "supported_formats": supported_formats
            },
            status_code=415
        )


class InvalidUrlError(VideoProcessingError):
    """无效的视频链接错误"""
    def __init__(self, url: str, reason: str = ""):
        super().__init__(
            message=f"无效的视频链接: {url}",
            error_code="INVALID_URL",
            details={
                "url": url,
                "reason": reason
            },
            status_code=400
        )


class VideoNotAccessibleError(VideoProcessingError):
    """视频不可访问错误"""
    def __init__(self, url: str, reason: str = ""):
        super().__init__(
            message=f"视频不可访问: {url}",
            error_code="VIDEO_NOT_ACCESSIBLE",
            details={
                "url": url,
                "reason": reason
            },
            status_code=404
        )


class CorruptedVideoError(VideoProcessingError):
    """视频文件损坏错误"""
    def __init__(self, video_path: str, reason: str = ""):
        super().__init__(
            message="视频文件损坏或格式不支持",
            error_code="CORRUPTED_VIDEO",
            details={
                "video_path": video_path,
                "reason": reason
            },
            status_code=400
        )


# 处理错误
class MetadataExtractionError(VideoProcessingError):
    """元数据提取失败错误"""
    def __init__(self, video_path: str, reason: str = ""):
        super().__init__(
            message="视频元数据提取失败",
            error_code="METADATA_EXTRACTION_ERROR",
            details={
                "video_path": video_path,
                "reason": reason
            },
            status_code=500
        )


class FrameExtractionError(VideoProcessingError):
    """视频帧提取失败错误"""
    def __init__(self, video_path: str, reason: str = ""):
        super().__init__(
            message="视频帧提取失败",
            error_code="FRAME_EXTRACTION_ERROR",
            details={
                "video_path": video_path,
                "reason": reason
            },
            status_code=500
        )


class FFmpegError(VideoProcessingError):
    """FFmpeg处理错误"""
    def __init__(self, command: str, stderr: str = "", returncode: int = 0):
        super().__init__(
            message="视频处理失败",
            error_code="FFMPEG_ERROR",
            details={
                "command": command,
                "stderr": stderr,
                "returncode": returncode
            },
            status_code=500
        )


class WatermarkRemovalError(VideoProcessingError):
    """水印去除失败错误"""
    def __init__(self, video_id: str, reason: str = ""):
        super().__init__(
            message="水印去除处理失败",
            error_code="WATERMARK_REMOVAL_ERROR",
            details={
                "video_id": video_id,
                "reason": reason
            },
            status_code=500
        )


# 授权错误
class InvalidTokenError(VideoProcessingError):
    """授权令牌无效或过期错误"""
    def __init__(self, token_id: str = "", reason: str = ""):
        super().__init__(
            message="授权令牌无效或已过期",
            error_code="INVALID_TOKEN",
            details={
                "token_id": token_id,
                "reason": reason
            },
            status_code=401
        )


class UnauthorizedAccessError(VideoProcessingError):
    """无权访问指定资源错误"""
    def __init__(self, resource: str, user_id: str = ""):
        super().__init__(
            message="无权访问指定资源",
            error_code="UNAUTHORIZED_ACCESS",
            details={
                "resource": resource,
                "user_id": user_id
            },
            status_code=403
        )


# 合规错误
class CopyrightNotConfirmedError(VideoProcessingError):
    """版权未确认错误"""
    def __init__(self, video_id: str):
        super().__init__(
            message="版权声明未确认，无法处理视频",
            error_code="COPYRIGHT_NOT_CONFIRMED",
            details={
                "video_id": video_id
            },
            status_code=403
        )


# 系统错误
class StorageError(VideoProcessingError):
    """存储操作失败错误"""
    def __init__(self, operation: str, path: str, reason: str = ""):
        super().__init__(
            message=f"存储操作失败: {operation}",
            error_code="STORAGE_ERROR",
            details={
                "operation": operation,
                "path": path,
                "reason": reason
            },
            status_code=500
        )


class TaskQueueError(VideoProcessingError):
    """任务队列错误"""
    def __init__(self, task_id: str, reason: str = ""):
        super().__init__(
            message="任务队列处理失败",
            error_code="TASK_QUEUE_ERROR",
            details={
                "task_id": task_id,
                "reason": reason
            },
            status_code=500
        )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    记录错误日志
    
    参数:
        error: 异常对象
        context: 上下文信息
    """
    context = context or {}
    
    if isinstance(error, VideoProcessingError):
        logger.error(
            f"[{error.error_code}] {error.message}",
            extra={
                "error_code": error.error_code,
                "details": error.details,
                "context": context
            }
        )
    else:
        logger.error(
            f"Unexpected error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "context": context
            },
            exc_info=True
        )


def create_error_response(
    error: Exception,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建标准化的错误响应
    
    参数:
        error: 异常对象
        request_id: 请求ID（可选）
        
    返回:
        Dict[str, Any]: 错误响应字典
    """
    if isinstance(error, VideoProcessingError):
        response = error.to_dict()
    else:
        response = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "details": {
                    "error_type": type(error).__name__,
                    "error_message": str(error)
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    return response
