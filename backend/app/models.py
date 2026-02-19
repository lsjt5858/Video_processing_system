"""
数据模型定义

使用Pydantic进行数据验证和序列化
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator, ConfigDict


class VideoFormat(str, Enum):
    """视频格式枚举"""
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"


class ProcessingMode(str, Enum):
    """处理模式枚举"""
    CROP_RECONSTRUCT = "crop_reconstruct"
    AI_INPAINTING = "ai_inpainting"
    BLUR_REPLACE = "blur_replace"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BoundingBox(BaseModel):
    """边界框"""
    x: int = Field(..., ge=0, description="左上角x坐标")
    y: int = Field(..., ge=0, description="左上角y坐标")
    width: int = Field(..., gt=0, description="宽度")
    height: int = Field(..., gt=0, description="高度")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "x": 100,
                "y": 50,
                "width": 200,
                "height": 100
            }
        }
    )


class VideoMetadata(BaseModel):
    """视频元数据"""
    video_id: str = Field(..., description="视频唯一标识")
    format: VideoFormat = Field(..., description="视频格式")
    resolution: Tuple[int, int] = Field(..., description="分辨率 (width, height)")
    duration: float = Field(..., gt=0, description="时长（秒）")
    codec: str = Field(..., description="编码格式，如h264, h265")
    framerate: float = Field(..., gt=0, description="帧率")
    bitrate: int = Field(..., gt=0, description="码率（bps）")
    file_size: int = Field(..., gt=0, description="文件大小（字节）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    @field_validator('resolution')
    @classmethod
    def validate_resolution(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        """验证分辨率"""
        if len(v) != 2:
            raise ValueError("分辨率必须是包含两个整数的元组 (width, height)")
        width, height = v
        if width <= 0 or height <= 0:
            raise ValueError("分辨率的宽度和高度必须大于0")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "video_id": "vid_123456",
                "format": "mp4",
                "resolution": [1920, 1080],
                "duration": 120.5,
                "codec": "h264",
                "framerate": 30.0,
                "bitrate": 5000000,
                "file_size": 104857600,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class WatermarkRegion(BaseModel):
    """水印区域"""
    region_id: str = Field(..., description="区域唯一标识")
    video_id: str = Field(..., description="所属视频ID")
    bbox: BoundingBox = Field(..., description="边界框")
    start_time: float = Field(..., ge=0, description="开始时间（秒）")
    end_time: float = Field(..., gt=0, description="结束时间（秒）")
    confidence: float = Field(..., ge=0, le=1, description="置信度 (0-1)")
    watermark_type: str = Field(..., description="水印类型: corner, rolling, logo, subtitle")
    detection_method: str = Field(..., description="检测方法: auto 或 manual")

    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v: float, info) -> float:
        """验证时间范围"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("结束时间必须大于开始时间")
        return v

    @field_validator('watermark_type')
    @classmethod
    def validate_watermark_type(cls, v: str) -> str:
        """验证水印类型"""
        valid_types = ["corner", "rolling", "logo", "subtitle"]
        if v not in valid_types:
            raise ValueError(f"水印类型必须是以下之一: {', '.join(valid_types)}")
        return v

    @field_validator('detection_method')
    @classmethod
    def validate_detection_method(cls, v: str) -> str:
        """验证检测方法"""
        valid_methods = ["auto", "manual"]
        if v not in valid_methods:
            raise ValueError(f"检测方法必须是以下之一: {', '.join(valid_methods)}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "region_id": "reg_123456",
                "video_id": "vid_123456",
                "bbox": {
                    "x": 100,
                    "y": 50,
                    "width": 200,
                    "height": 100
                },
                "start_time": 0.0,
                "end_time": 120.5,
                "confidence": 0.95,
                "watermark_type": "corner",
                "detection_method": "auto"
            }
        }
    )


class ProcessingTask(BaseModel):
    """处理任务"""
    task_id: str = Field(..., description="任务唯一标识")
    user_id: str = Field(..., description="用户ID")
    video_id: str = Field(..., description="视频ID")
    task_type: str = Field(..., description="任务类型: detection, removal, optimization")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    result: Optional[Dict[str, Any]] = Field(None, description="处理结果")

    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        """验证任务类型"""
        valid_types = ["detection", "removal", "optimization"]
        if v not in valid_types:
            raise ValueError(f"任务类型必须是以下之一: {', '.join(valid_types)}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_123456",
                "user_id": "user_123",
                "video_id": "vid_123456",
                "task_type": "removal",
                "status": "pending",
                "parameters": {
                    "mode": "crop_reconstruct",
                    "regions": []
                },
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": None,
                "completed_at": None,
                "error_message": None,
                "result": None
            }
        }
    )


# 辅助模型 - 用于API请求和响应

class VideoImportResult(BaseModel):
    """视频导入结果"""
    video_id: str
    metadata: VideoMetadata
    storage_path: str
    import_source: str = Field(..., description="导入来源: local, platform, url")
    import_time: datetime = Field(default_factory=datetime.now)


class DetectionResult(BaseModel):
    """水印检测结果"""
    video_id: str
    watermarks: List[WatermarkRegion]
    detection_time: datetime = Field(default_factory=datetime.now)
    processing_duration: float = Field(..., description="处理耗时（秒）")


class RemovalResult(BaseModel):
    """水印去除结果"""
    video_id: str
    output_video_id: str
    output_path: str
    processing_mode: ProcessingMode
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="质量评分 (0-100)")
    processing_duration: float = Field(..., description="处理耗时（秒）")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="处理参数")


class OptimizationResult(BaseModel):
    """视频优化结果"""
    video_id: str
    output_video_id: str
    output_path: str
    optimization_type: str = Field(..., description="优化类型: dedup_compress, upscale, fix_framerate, optimize_bitrate")
    original_size: int = Field(..., gt=0, description="原始文件大小（字节）")
    optimized_size: int = Field(..., gt=0, description="优化后文件大小（字节）")
    quality_score: float = Field(..., ge=0, le=100, description="质量评分 (0-100)")
    processing_duration: float = Field(..., description="处理耗时（秒）")


class CopyrightDeclaration(BaseModel):
    """版权声明"""
    declaration_id: str
    user_id: str
    video_id: str
    confirmed: bool
    confirmation_time: datetime
    ip_address: str
    declaration_text: str


class AuthorizationToken(BaseModel):
    """授权令牌"""
    token_id: str
    user_id: str
    platform: str = Field(..., description="平台名称: youtube, tiktok等")
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime
    scope: List[str] = Field(default_factory=list, description="授权范围")
    created_at: datetime = Field(default_factory=datetime.now)
    last_validated: datetime = Field(default_factory=datetime.now)


class OperationLog(BaseModel):
    """操作日志"""
    log_id: str
    user_id: str
    operation_type: str = Field(..., description="操作类型: upload, detect, remove, optimize, export")
    video_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: str
    details: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = Field(..., description="风险等级: low, medium, high")

    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """验证风险等级"""
        valid_levels = ["low", "medium", "high"]
        if v not in valid_levels:
            raise ValueError(f"风险等级必须是以下之一: {', '.join(valid_levels)}")
        return v


class BatchJob(BaseModel):
    """批量任务"""
    job_id: str
    user_id: str
    job_type: str = Field(..., description="任务类型: upload, detect, process, export")
    total_count: int = Field(..., ge=0)
    completed_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    tasks: List[ProcessingTask] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
