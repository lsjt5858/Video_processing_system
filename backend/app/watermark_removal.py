"""
水印去除模块

实现多种水印去除策略：
1. 裁剪重构模式 (crop_reconstruct)
2. AI修复填充模式 (ai_inpainting) - 待实现
3. 局部模糊替换模式 (blur_replace) - 待实现
"""

import os
import uuid
import subprocess
import time
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from .models import WatermarkRegion, RemovalResult, ProcessingMode, BoundingBox


class WatermarkRemovalEngine:
    """水印去除引擎"""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        初始化水印去除引擎
        
        参数:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def crop_reconstruct(
        self,
        video_path: str,
        video_id: str,
        regions: List[WatermarkRegion],
        video_metadata: Dict[str, Any]
    ) -> RemovalResult:
        """
        裁剪重构模式去除水印
        
        参数:
            video_path: 输入视频路径
            video_id: 视频ID
            regions: 水印区域列表
            video_metadata: 视频元数据（包含分辨率、编码等信息）
        
        返回:
            RemovalResult: 包含处理后视频路径、裁剪参数、主体完整度
        
        说明:
            - 分析视频主体区域
            - 推荐裁剪比例以排除水印
            - 确保主体内容完整度不低于90%
            - 保持原始帧率和编码格式
        """
        start_time = time.time()
        
        # 获取实际视频分辨率（从实际文件中提取）
        actual_width, actual_height = self._get_actual_video_resolution(video_path)
        
        # 使用实际分辨率，如果提取失败则使用元数据
        video_width = actual_width if actual_width else video_metadata.get('resolution_width', 1920)
        video_height = actual_height if actual_height else video_metadata.get('resolution_height', 1080)
        
        # 分析水印位置，计算最优裁剪区域
        crop_params = self._calculate_optimal_crop(
            regions, video_width, video_height
        )
        
        # 验证主体完整度
        content_integrity = crop_params['content_integrity']
        if content_integrity < 0.90:
            raise ValueError(
                f"裁剪后主体内容完整度 {content_integrity:.2%} 低于要求的90%"
            )
        
        # 生成输出文件路径
        output_video_id = f"crop_{uuid.uuid4().hex[:12]}"
        output_filename = f"{output_video_id}.mp4"
        output_path = self.output_dir / output_filename
        
        # 使用FFmpeg执行视频裁剪
        self._execute_ffmpeg_crop(
            input_path=video_path,
            output_path=str(output_path),
            crop_x=crop_params['crop_x'],
            crop_y=crop_params['crop_y'],
            crop_width=crop_params['crop_width'],
            crop_height=crop_params['crop_height'],
            codec=video_metadata.get('codec', 'h264'),
            framerate=video_metadata.get('framerate', 30.0)
        )
        
        processing_duration = time.time() - start_time
        
        # 构建返回结果
        result = RemovalResult(
            video_id=video_id,
            output_video_id=output_video_id,
            output_path=str(output_path),
            processing_mode=ProcessingMode.CROP_RECONSTRUCT,
            quality_score=None,  # 裁剪模式不需要质量评分
            processing_duration=processing_duration,
            parameters={
                'crop_x': crop_params['crop_x'],
                'crop_y': crop_params['crop_y'],
                'crop_width': crop_params['crop_width'],
                'crop_height': crop_params['crop_height'],
                'content_integrity': content_integrity,
                'original_resolution': (video_width, video_height),
                'cropped_resolution': (crop_params['crop_width'], crop_params['crop_height'])
            }
        )
        
        return result
    
    def _get_actual_video_resolution(self, video_path: str) -> Tuple[Optional[int], Optional[int]]:
        """
        从视频文件中提取实际分辨率
        
        参数:
            video_path: 视频文件路径
        
        返回:
            Tuple[Optional[int], Optional[int]]: (width, height) 或 (None, None)
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split(','))
            return width, height
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return None, None
    
    def _calculate_optimal_crop(
        self,
        regions: List[WatermarkRegion],
        video_width: int,
        video_height: int
    ) -> Dict[str, Any]:
        """
        计算最优裁剪区域
        
        参数:
            regions: 水印区域列表
            video_width: 视频宽度
            video_height: 视频高度
        
        返回:
            Dict: 包含裁剪参数和主体完整度的字典
        """
        if not regions:
            # 没有水印区域，返回原始尺寸
            return {
                'crop_x': 0,
                'crop_y': 0,
                'crop_width': video_width,
                'crop_height': video_height,
                'content_integrity': 1.0
            }
        
        # 收集所有水印区域的边界
        watermark_bounds = []
        for region in regions:
            bbox = region.bbox
            # 确保水印边界不超出视频范围
            left = max(0, bbox.x)
            right = min(video_width, bbox.x + bbox.width)
            top = max(0, bbox.y)
            bottom = min(video_height, bbox.y + bbox.height)
            
            watermark_bounds.append({
                'left': left,
                'right': right,
                'top': top,
                'bottom': bottom
            })
        
        # 分析水印位置，确定裁剪策略
        # 策略：找到能排除所有水印的最大矩形区域
        
        # 计算水印的整体边界
        min_left = min(wb['left'] for wb in watermark_bounds)
        max_right = max(wb['right'] for wb in watermark_bounds)
        min_top = min(wb['top'] for wb in watermark_bounds)
        max_bottom = max(wb['bottom'] for wb in watermark_bounds)
        
        # 尝试不同的裁剪策略，选择保留面积最大的
        strategies = []
        
        # 策略1: 裁剪掉左边（如果水印在左侧）
        if min_left < video_width * 0.3:  # 水印在左侧30%区域
            crop_left = max_right
            if crop_left < video_width:
                crop_width = video_width - crop_left
                if crop_width > 0:
                    strategies.append({
                        'crop_x': crop_left,
                        'crop_y': 0,
                        'crop_width': crop_width,
                        'crop_height': video_height,
                        'area': crop_width * video_height
                    })
        
        # 策略2: 裁剪掉右边（如果水印在右侧）
        if max_right > video_width * 0.7:  # 水印在右侧30%区域
            crop_width = min_left
            if crop_width > 0:
                strategies.append({
                    'crop_x': 0,
                    'crop_y': 0,
                    'crop_width': crop_width,
                    'crop_height': video_height,
                    'area': crop_width * video_height
                })
        
        # 策略3: 裁剪掉上边（如果水印在顶部）
        if min_top < video_height * 0.3:  # 水印在顶部30%区域
            crop_top = max_bottom
            if crop_top < video_height:
                crop_height = video_height - crop_top
                if crop_height > 0:
                    strategies.append({
                        'crop_x': 0,
                        'crop_y': crop_top,
                        'crop_width': video_width,
                        'crop_height': crop_height,
                        'area': video_width * crop_height
                    })
        
        # 策略4: 裁剪掉下边（如果水印在底部）
        if max_bottom > video_height * 0.7:  # 水印在底部30%区域
            crop_height = min_top
            if crop_height > 0:
                strategies.append({
                    'crop_x': 0,
                    'crop_y': 0,
                    'crop_width': video_width,
                    'crop_height': crop_height,
                    'area': video_width * crop_height
                })
        
        # 策略5: 裁剪掉角落（如果水印在角落）
        # 左上角
        if min_left < video_width * 0.3 and min_top < video_height * 0.3:
            crop_width = video_width - max_right
            crop_height = video_height - max_bottom
            if crop_width > 0 and crop_height > 0:
                strategies.append({
                    'crop_x': max_right,
                    'crop_y': max_bottom,
                    'crop_width': crop_width,
                    'crop_height': crop_height,
                    'area': crop_width * crop_height
                })
        
        # 右上角
        if max_right > video_width * 0.7 and min_top < video_height * 0.3:
            crop_width = min_left
            crop_height = video_height - max_bottom
            if crop_width > 0 and crop_height > 0:
                strategies.append({
                    'crop_x': 0,
                    'crop_y': max_bottom,
                    'crop_width': crop_width,
                    'crop_height': crop_height,
                    'area': crop_width * crop_height
                })
        
        # 左下角
        if min_left < video_width * 0.3 and max_bottom > video_height * 0.7:
            crop_width = video_width - max_right
            crop_height = min_top
            if crop_width > 0 and crop_height > 0:
                strategies.append({
                    'crop_x': max_right,
                    'crop_y': 0,
                    'crop_width': crop_width,
                    'crop_height': crop_height,
                    'area': crop_width * crop_height
                })
        
        # 右下角
        if max_right > video_width * 0.7 and max_bottom > video_height * 0.7:
            crop_width = min_left
            crop_height = min_top
            if crop_width > 0 and crop_height > 0:
                strategies.append({
                    'crop_x': 0,
                    'crop_y': 0,
                    'crop_width': crop_width,
                    'crop_height': crop_height,
                    'area': crop_width * crop_height
                })
        
        # 如果没有合适的策略，使用中心裁剪
        if not strategies:
            # 计算排除水印后的中心区域
            safe_left = max_right if max_right < video_width * 0.5 else 0
            safe_right = min_left if min_left > video_width * 0.5 else video_width
            safe_top = max_bottom if max_bottom < video_height * 0.5 else 0
            safe_bottom = min_top if min_top > video_height * 0.5 else video_height
            
            crop_width = safe_right - safe_left
            crop_height = safe_bottom - safe_top
            
            if crop_width > 0 and crop_height > 0:
                strategies.append({
                    'crop_x': safe_left,
                    'crop_y': safe_top,
                    'crop_width': crop_width,
                    'crop_height': crop_height,
                    'area': crop_width * crop_height
                })
        
        # 如果仍然没有策略（极端情况），返回原始尺寸
        if not strategies:
            return {
                'crop_x': 0,
                'crop_y': 0,
                'crop_width': video_width,
                'crop_height': video_height,
                'content_integrity': 1.0
            }
        
        # 选择保留面积最大的策略
        best_strategy = max(strategies, key=lambda s: s['area'])
        
        # 计算主体完整度（保留面积 / 原始面积）
        original_area = video_width * video_height
        content_integrity = best_strategy['area'] / original_area
        
        # 确保裁剪尺寸是偶数（视频编码要求）
        best_strategy['crop_width'] = (best_strategy['crop_width'] // 2) * 2
        best_strategy['crop_height'] = (best_strategy['crop_height'] // 2) * 2
        
        # 添加主体完整度
        best_strategy['content_integrity'] = content_integrity
        
        return best_strategy
    
    def _execute_ffmpeg_crop(
        self,
        input_path: str,
        output_path: str,
        crop_x: int,
        crop_y: int,
        crop_width: int,
        crop_height: int,
        codec: str,
        framerate: float
    ) -> None:
        """
        使用FFmpeg执行视频裁剪
        
        参数:
            input_path: 输入视频路径
            output_path: 输出视频路径
            crop_x: 裁剪起始x坐标
            crop_y: 裁剪起始y坐标
            crop_width: 裁剪宽度
            crop_height: 裁剪高度
            codec: 视频编码格式
            framerate: 帧率
        """
        # 构建FFmpeg命令
        # 使用crop滤镜: crop=width:height:x:y
        # -c:v copy 保持原始编码（如果可能）
        # -r 保持原始帧率
        
        # 映射编码格式
        codec_map = {
            'h264': 'libx264',
            'h265': 'libx265',
            'hevc': 'libx265',
            'vp9': 'libvpx-vp9',
            'vp8': 'libvpx'
        }
        
        video_codec = codec_map.get(codec.lower(), 'libx264')
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f'crop={crop_width}:{crop_height}:{crop_x}:{crop_y}',
            '-c:v', video_codec,
            '-r', str(framerate),
            '-c:a', 'copy',  # 音频直接复制
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        try:
            # 执行FFmpeg命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"FFmpeg裁剪失败: {e.stderr}"
            )
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg未安装或不在系统PATH中"
            )


# 创建全局实例
removal_engine = WatermarkRemovalEngine()
