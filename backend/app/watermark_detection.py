"""
水印检测模块

提供视频帧提取、缩略图生成和水印检测功能
"""

import os
import cv2
import uuid
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

from .models import WatermarkRegion, BoundingBox, DetectionResult
from .errors import FrameExtractionError, CorruptedVideoError, log_error
from .cache_manager import (
    cache_frames,
    get_cached_frames,
    cache_thumbnail,
    get_cached_thumbnail,
    cache_video_metadata,
    get_cached_metadata
)


# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
THUMBNAIL_DIR = BASE_DIR / "thumbnails"


async def extract_key_frames(
    video_path: str,
    num_frames: int = 10,
    save_thumbnails: bool = True,
    use_cache: bool = True
) -> List[Tuple[int, str]]:
    """
    从视频中提取关键帧（优化版：使用FFmpeg + 缓存）
    
    参数:
        video_path: 视频文件路径
        num_frames: 要提取的帧数量（默认10帧）
        save_thumbnails: 是否保存缩略图（默认True）
        use_cache: 是否使用缓存（默认True）
        
    返回:
        List[Tuple[int, str]]: 帧列表，每个元素为 (帧索引, 缩略图路径)
        
    异常:
        FrameExtractionError: 帧提取失败
    """
    video_id = Path(video_path).stem
    
    # 检查缓存
    if use_cache:
        cached_frames = await get_cached_frames(video_id)
        if cached_frames:
            # 验证缓存的文件是否存在
            all_exist = all(Path(frame[1]).exists() for frame in cached_frames if frame[1])
            if all_exist:
                return cached_frames
    
    try:
        # 使用FFmpeg提取帧（比OpenCV快）
        # 首先获取视频信息
        probe_cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'v:0',
            video_path
        ]
        
        probe_result = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if probe_result.returncode != 0:
            raise FrameExtractionError(f"无法获取视频信息: {probe_result.stderr}")
        
        probe_data = json.loads(probe_result.stdout)
        if not probe_data.get('streams'):
            raise FrameExtractionError("未找到视频流")
        
        stream = probe_data['streams'][0]
        
        # 获取总帧数和帧率
        nb_frames = int(stream.get('nb_frames', 0))
        fps_str = stream.get('r_frame_rate', '30/1')
        try:
            num, den = map(int, fps_str.split('/'))
            fps = num / den if den != 0 else 30.0
        except:
            fps = 30.0
        
        # 如果无法从流中获取帧数，使用时长计算
        if nb_frames == 0:
            duration = float(stream.get('duration', 0))
            if duration > 0:
                nb_frames = int(duration * fps)
        
        if nb_frames == 0:
            raise FrameExtractionError("无法确定视频帧数")
        
        # 计算要提取的帧索引（均匀分布）
        if num_frames >= nb_frames:
            frame_indices = list(range(nb_frames))
        else:
            step = nb_frames / num_frames
            frame_indices = [int(i * step) for i in range(num_frames)]
        
        # 使用FFmpeg批量提取帧（更快）
        extracted_frames = []
        
        for frame_idx in frame_indices:
            # 检查缩略图缓存
            if use_cache:
                cached_thumb = await get_cached_thumbnail(video_id, frame_idx)
                if cached_thumb and Path(cached_thumb).exists():
                    extracted_frames.append((frame_idx, cached_thumb))
                    continue
            
            if save_thumbnails:
                thumbnail_filename = f"{video_id}_frame_{frame_idx}.jpg"
                thumbnail_path = THUMBNAIL_DIR / thumbnail_filename
                
                # 计算时间戳
                timestamp = frame_idx / fps
                
                # 使用FFmpeg提取单帧（使用scale滤镜调整大小）
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-ss', str(timestamp),
                    '-i', video_path,
                    '-vframes', '1',
                    '-vf', 'scale=800:-1',  # 宽度800，高度自动
                    '-q:v', '2',  # 高质量
                    '-y',  # 覆盖输出文件
                    str(thumbnail_path)
                ]
                
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and thumbnail_path.exists():
                    extracted_frames.append((frame_idx, str(thumbnail_path)))
                    
                    # 缓存缩略图路径
                    if use_cache:
                        await cache_thumbnail(video_id, frame_idx, str(thumbnail_path))
                else:
                    print(f"警告: 无法提取帧 {frame_idx}")
            else:
                extracted_frames.append((frame_idx, None))
        
        if not extracted_frames:
            raise FrameExtractionError("未能提取任何帧")
        
        # 缓存提取的帧列表
        if use_cache:
            await cache_frames(video_id, extracted_frames)
        
        return extracted_frames
        
    except subprocess.TimeoutExpired:
        raise FrameExtractionError("帧提取超时")
    except json.JSONDecodeError as e:
        raise FrameExtractionError(f"解析视频信息失败: {str(e)}")
    except Exception as e:
        raise FrameExtractionError(f"帧提取失败: {str(e)}")


async def generate_thumbnail(
    video_path: str,
    timestamp: float = 0.0,
    max_width: int = 800
) -> str:
    """
    生成视频缩略图（从指定时间点）
    
    参数:
        video_path: 视频文件路径
        timestamp: 时间戳（秒），默认0.0（第一帧）
        max_width: 缩略图最大宽度（默认800像素）
        
    返回:
        str: 缩略图文件路径
        
    异常:
        FrameExtractionError: 缩略图生成失败
    """
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise FrameExtractionError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        # 验证时间戳
        if timestamp < 0 or timestamp > duration:
            timestamp = 0.0
        
        # 设置视频位置到指定时间
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # 读取帧
        ret, frame = cap.read()
        
        if not ret:
            raise FrameExtractionError(f"无法读取时间戳 {timestamp} 处的帧")
        
        # 调整大小
        height, width = frame.shape[:2]
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # 生成唯一的文件名
        video_id = Path(video_path).stem
        thumbnail_filename = f"{video_id}_thumb_{uuid.uuid4().hex[:8]}.jpg"
        thumbnail_path = THUMBNAIL_DIR / thumbnail_filename
        
        # 保存缩略图
        cv2.imwrite(str(thumbnail_path), frame)
        
        # 释放视频资源
        cap.release()
        
        return str(thumbnail_path)
        
    except cv2.error as e:
        raise FrameExtractionError(f"OpenCV错误: {str(e)}")
    except Exception as e:
        raise FrameExtractionError(f"缩略图生成失败: {str(e)}")


async def get_frame_at_time(
    video_path: str,
    timestamp: float
) -> Tuple[bool, Optional[any]]:
    """
    获取视频指定时间点的帧数据
    
    参数:
        video_path: 视频文件路径
        timestamp: 时间戳（秒）
        
    返回:
        Tuple[bool, Optional[numpy.ndarray]]: (成功标志, 帧数据)
    """
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return False, None
        
        # 获取FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 设置视频位置
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # 读取帧
        ret, frame = cap.read()
        
        # 释放资源
        cap.release()
        
        return ret, frame if ret else None
        
    except Exception as e:
        print(f"获取帧失败: {str(e)}")
        return False, None


async def extract_frames_for_preview(
    video_path: str,
    video_id: str,
    num_frames: int = 10
) -> List[dict]:
    """
    提取视频帧用于预览（返回帧信息）
    
    参数:
        video_path: 视频文件路径
        video_id: 视频ID
        num_frames: 要提取的帧数量
        
    返回:
        List[dict]: 帧信息列表，每个元素包含 frame_index, timestamp, thumbnail_url
    """
    try:
        # 提取关键帧
        frames = await extract_key_frames(video_path, num_frames, save_thumbnails=True)
        
        # 打开视频获取FPS信息
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        # 构建帧信息列表
        frame_info_list = []
        for frame_idx, thumbnail_path in frames:
            timestamp = frame_idx / fps if fps > 0 else 0
            
            # 生成缩略图URL（相对路径）
            thumbnail_filename = Path(thumbnail_path).name
            thumbnail_url = f"/thumbnails/{thumbnail_filename}"
            
            frame_info_list.append({
                "frame_index": frame_idx,
                "timestamp": round(timestamp, 2),
                "thumbnail_url": thumbnail_url
            })
        
        return frame_info_list
        
    except Exception as e:
        raise FrameExtractionError(f"提取预览帧失败: {str(e)}")


async def validate_bounding_box(
    bbox: BoundingBox,
    video_width: int,
    video_height: int
) -> bool:
    """
    验证边界框坐标是否有效
    
    参数:
        bbox: 边界框对象
        video_width: 视频宽度
        video_height: 视频高度
        
    返回:
        bool: 边界框是否有效
    """
    # 检查坐标是否为负数
    if bbox.x < 0 or bbox.y < 0:
        return False
    
    # 检查宽度和高度是否为正数
    if bbox.width <= 0 or bbox.height <= 0:
        return False
    
    # 检查边界框是否超出视频范围
    if bbox.x + bbox.width > video_width:
        return False
    
    if bbox.y + bbox.height > video_height:
        return False
    
    return True


async def save_manual_watermark_region(
    db,
    video_id: str,
    bbox: BoundingBox,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
    watermark_type: str = "manual",
    video_duration: Optional[float] = None
) -> WatermarkRegion:
    """
    保存手动标记的水印区域到数据库
    
    参数:
        db: 数据库会话
        video_id: 视频ID
        bbox: 边界框
        start_time: 开始时间（秒），默认0.0
        end_time: 结束时间（秒），如果为None则使用视频总时长
        watermark_type: 水印类型，默认"manual"
        video_duration: 视频总时长（秒），用于设置默认end_time
        
    返回:
        WatermarkRegion: 保存的水印区域对象
        
    异常:
        ValueError: 参数验证失败
    """
    from . import crud
    
    # 如果未提供end_time，使用视频总时长
    if end_time is None:
        if video_duration is None:
            raise ValueError("必须提供end_time或video_duration")
        end_time = video_duration
    
    # 验证时间范围
    if start_time < 0:
        raise ValueError("开始时间不能为负数")
    
    if end_time <= start_time:
        raise ValueError("结束时间必须大于开始时间")
    
    # 生成唯一的区域ID
    region_id = f"reg_{uuid.uuid4().hex[:12]}"
    
    # 创建水印区域记录
    region = await crud.create_watermark_region(
        db=db,
        region_id=region_id,
        video_id=video_id,
        bbox_x=bbox.x,
        bbox_y=bbox.y,
        bbox_width=bbox.width,
        bbox_height=bbox.height,
        start_time=start_time,
        end_time=end_time,
        confidence=1.0,  # 手动标记的置信度为1.0
        watermark_type=watermark_type,
        detection_method="manual"
    )
    
    return region


async def mark_watermark_regions(
    db,
    video_id: str,
    video_path: str,
    bounding_boxes: List[dict]
) -> List[WatermarkRegion]:
    """
    批量标记水印区域
    
    参数:
        db: 数据库会话
        video_id: 视频ID
        video_path: 视频文件路径
        bounding_boxes: 边界框列表，每个元素包含 x, y, width, height, start_time, end_time, watermark_type
        
    返回:
        List[WatermarkRegion]: 保存的水印区域列表
        
    异常:
        ValueError: 边界框验证失败
        FrameExtractionError: 无法获取视频信息
    """
    try:
        # 获取视频信息
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise FrameExtractionError(f"无法打开视频文件: {video_path}")
        
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps if fps > 0 else 0
        
        cap.release()
        
        # 保存所有水印区域
        saved_regions = []
        
        for bbox_data in bounding_boxes:
            # 创建BoundingBox对象
            bbox = BoundingBox(
                x=bbox_data.get("x", 0),
                y=bbox_data.get("y", 0),
                width=bbox_data.get("width", 0),
                height=bbox_data.get("height", 0)
            )
            
            # 验证边界框
            if not await validate_bounding_box(bbox, video_width, video_height):
                raise ValueError(
                    f"无效的边界框: x={bbox.x}, y={bbox.y}, "
                    f"width={bbox.width}, height={bbox.height}, "
                    f"视频尺寸: {video_width}x{video_height}"
                )
            
            # 获取时间范围和水印类型
            start_time = bbox_data.get("start_time", 0.0)
            end_time = bbox_data.get("end_time", video_duration)
            watermark_type = bbox_data.get("watermark_type", "manual")
            
            # 保存水印区域
            region = await save_manual_watermark_region(
                db=db,
                video_id=video_id,
                bbox=bbox,
                start_time=start_time,
                end_time=end_time,
                watermark_type=watermark_type,
                video_duration=video_duration
            )
            
            saved_regions.append(region)
        
        return saved_regions
        
    except cv2.error as e:
        raise FrameExtractionError(f"OpenCV错误: {str(e)}")
    except Exception as e:
        if isinstance(e, (ValueError, FrameExtractionError)):
            raise
        raise FrameExtractionError(f"标记水印区域失败: {str(e)}")


async def batch_extract_frames(
    video_paths: List[Tuple[str, str]],
    num_frames: int = 10
) -> dict:
    """
    批量提取多个视频的预览帧
    
    参数:
        video_paths: 视频路径列表，每个元素为 (video_id, video_path)
        num_frames: 每个视频要提取的帧数量（默认10帧）
        
    返回:
        dict: 批量提取结果，格式为 {
            "total_count": 总视频数,
            "success_count": 成功数,
            "failed_count": 失败数,
            "results": [
                {
                    "video_id": "视频ID",
                    "status": "success" 或 "failed",
                    "frames": [...] 或 None,
                    "error": "错误信息" 或 None
                }
            ]
        }
    """
    results = []
    success_count = 0
    failed_count = 0
    
    for video_id, video_path in video_paths:
        try:
            # 提取预览帧
            frames = await extract_frames_for_preview(
                video_path=video_path,
                video_id=video_id,
                num_frames=num_frames
            )
            
            results.append({
                "video_id": video_id,
                "status": "success",
                "frames": frames,
                "error": None
            })
            success_count += 1
            
        except Exception as e:
            results.append({
                "video_id": video_id,
                "status": "failed",
                "frames": None,
                "error": str(e)
            })
            failed_count += 1
    
    return {
        "total_count": len(video_paths),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }


async def batch_mark_watermarks(
    db,
    watermark_data: List[dict]
) -> dict:
    """
    批量标记多个视频的水印区域
    
    参数:
        db: 数据库会话
        watermark_data: 水印数据列表，每个元素包含:
            - video_id: 视频ID
            - video_path: 视频文件路径
            - bounding_boxes: 边界框列表
            
    返回:
        dict: 批量标记结果，格式为 {
            "total_count": 总视频数,
            "success_count": 成功数,
            "failed_count": 失败数,
            "results": [
                {
                    "video_id": "视频ID",
                    "status": "success" 或 "failed",
                    "regions": [...] 或 None,
                    "error": "错误信息" 或 None
                }
            ]
        }
    """
    results = []
    success_count = 0
    failed_count = 0
    
    for data in watermark_data:
        video_id = data.get("video_id")
        video_path = data.get("video_path")
        bounding_boxes = data.get("bounding_boxes", [])
        
        try:
            # 标记水印区域
            regions = await mark_watermark_regions(
                db=db,
                video_id=video_id,
                video_path=video_path,
                bounding_boxes=bounding_boxes
            )
            
            # 转换为字典格式
            regions_dict = [
                {
                    "region_id": r.region_id,
                    "video_id": r.video_id,
                    "bbox": {
                        "x": r.bbox.x,
                        "y": r.bbox.y,
                        "width": r.bbox.width,
                        "height": r.bbox.height
                    },
                    "start_time": r.start_time,
                    "end_time": r.end_time,
                    "confidence": r.confidence,
                    "watermark_type": r.watermark_type,
                    "detection_method": r.detection_method
                }
                for r in regions
            ]
            
            results.append({
                "video_id": video_id,
                "status": "success",
                "regions": regions_dict,
                "error": None
            })
            success_count += 1
            
        except Exception as e:
            results.append({
                "video_id": video_id,
                "status": "failed",
                "regions": None,
                "error": str(e)
            })
            failed_count += 1
    
    return {
        "total_count": len(watermark_data),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }
