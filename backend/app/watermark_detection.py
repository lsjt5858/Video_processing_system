"""
水印检测模块

提供视频帧提取、缩略图生成和水印检测功能
"""

import os
import cv2
import uuid
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

from .models import WatermarkRegion, BoundingBox, DetectionResult


# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
THUMBNAIL_DIR = BASE_DIR / "thumbnails"


class FrameExtractionError(Exception):
    """帧提取错误"""
    pass


async def extract_key_frames(
    video_path: str,
    num_frames: int = 10,
    save_thumbnails: bool = True
) -> List[Tuple[int, str]]:
    """
    从视频中提取关键帧
    
    参数:
        video_path: 视频文件路径
        num_frames: 要提取的帧数量（默认10帧）
        save_thumbnails: 是否保存缩略图（默认True）
        
    返回:
        List[Tuple[int, str]]: 帧列表，每个元素为 (帧索引, 缩略图路径)
        
    异常:
        FrameExtractionError: 帧提取失败
    """
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise FrameExtractionError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if total_frames == 0:
            raise FrameExtractionError("视频帧数为0")
        
        # 计算要提取的帧索引（均匀分布）
        frame_indices = []
        if num_frames >= total_frames:
            # 如果请求的帧数大于等于总帧数，提取所有帧
            frame_indices = list(range(total_frames))
        else:
            # 均匀分布提取帧
            step = total_frames / num_frames
            frame_indices = [int(i * step) for i in range(num_frames)]
        
        # 提取帧并保存缩略图
        extracted_frames = []
        video_id = Path(video_path).stem
        
        for frame_idx in frame_indices:
            # 设置视频位置到指定帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            
            # 读取帧
            ret, frame = cap.read()
            
            if not ret:
                print(f"警告: 无法读取帧 {frame_idx}")
                continue
            
            # 保存缩略图
            if save_thumbnails:
                thumbnail_filename = f"{video_id}_frame_{frame_idx}.jpg"
                thumbnail_path = THUMBNAIL_DIR / thumbnail_filename
                
                # 生成缩略图（调整大小以减小文件大小）
                height, width = frame.shape[:2]
                max_width = 800
                if width > max_width:
                    scale = max_width / width
                    new_width = max_width
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # 保存缩略图
                cv2.imwrite(str(thumbnail_path), frame)
                
                extracted_frames.append((frame_idx, str(thumbnail_path)))
            else:
                extracted_frames.append((frame_idx, None))
        
        # 释放视频资源
        cap.release()
        
        if not extracted_frames:
            raise FrameExtractionError("未能提取任何帧")
        
        return extracted_frames
        
    except cv2.error as e:
        raise FrameExtractionError(f"OpenCV错误: {str(e)}")
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
