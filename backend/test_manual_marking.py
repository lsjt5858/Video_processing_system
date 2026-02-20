"""
测试手动水印标记功能

验证手动标记功能的核心逻辑
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# 添加backend/app到Python路径
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.models import BoundingBox
from app.watermark_detection import (
    validate_bounding_box,
    save_manual_watermark_region,
    mark_watermark_regions
)


class TestBoundingBoxValidation:
    """测试边界框验证功能"""
    
    @pytest.mark.asyncio
    async def test_valid_bounding_box(self):
        """测试有效的边界框"""
        bbox = BoundingBox(x=100, y=50, width=200, height=100)
        video_width = 1920
        video_height = 1080
        
        result = await validate_bounding_box(bbox, video_width, video_height)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_negative_coordinates(self):
        """测试负坐标的边界框 - Pydantic会在模型层面拒绝"""
        # Pydantic会在创建BoundingBox时就抛出验证错误
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            bbox = BoundingBox(x=-10, y=50, width=200, height=100)
    
    @pytest.mark.asyncio
    async def test_zero_width(self):
        """测试宽度为0的边界框 - Pydantic会在模型层面拒绝"""
        # Pydantic会在创建BoundingBox时就抛出验证错误
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            bbox = BoundingBox(x=100, y=50, width=0, height=100)
    
    @pytest.mark.asyncio
    async def test_exceeds_video_width(self):
        """测试超出视频宽度的边界框"""
        bbox = BoundingBox(x=1800, y=50, width=200, height=100)
        video_width = 1920
        video_height = 1080
        
        result = await validate_bounding_box(bbox, video_width, video_height)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_exceeds_video_height(self):
        """测试超出视频高度的边界框"""
        bbox = BoundingBox(x=100, y=1000, width=200, height=100)
        video_width = 1920
        video_height = 1080
        
        result = await validate_bounding_box(bbox, video_width, video_height)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_boundary_edge_case(self):
        """测试边界情况：边界框刚好在视频边缘"""
        bbox = BoundingBox(x=1720, y=980, width=200, height=100)
        video_width = 1920
        video_height = 1080
        
        result = await validate_bounding_box(bbox, video_width, video_height)
        assert result is True


class TestManualWatermarkRegion:
    """测试手动水印区域保存功能"""
    
    @pytest.mark.asyncio
    async def test_save_with_default_end_time(self):
        """测试使用默认结束时间保存水印区域"""
        # 这个测试需要数据库mock，这里只验证参数验证逻辑
        bbox = BoundingBox(x=100, y=50, width=200, height=100)
        
        # 测试缺少end_time和video_duration时抛出异常
        with pytest.raises(ValueError, match="必须提供end_time或video_duration"):
            await save_manual_watermark_region(
                db=None,  # Mock
                video_id="test_video",
                bbox=bbox,
                start_time=0.0,
                end_time=None,
                video_duration=None
            )
    
    @pytest.mark.asyncio
    async def test_invalid_start_time(self):
        """测试负数开始时间"""
        bbox = BoundingBox(x=100, y=50, width=200, height=100)
        
        with pytest.raises(ValueError, match="开始时间不能为负数"):
            await save_manual_watermark_region(
                db=None,  # Mock
                video_id="test_video",
                bbox=bbox,
                start_time=-1.0,
                end_time=10.0
            )
    
    @pytest.mark.asyncio
    async def test_invalid_time_range(self):
        """测试结束时间小于等于开始时间"""
        bbox = BoundingBox(x=100, y=50, width=200, height=100)
        
        with pytest.raises(ValueError, match="结束时间必须大于开始时间"):
            await save_manual_watermark_region(
                db=None,  # Mock
                video_id="test_video",
                bbox=bbox,
                start_time=10.0,
                end_time=5.0
            )


def test_bounding_box_model():
    """测试BoundingBox模型验证"""
    # 有效的边界框
    bbox = BoundingBox(x=100, y=50, width=200, height=100)
    assert bbox.x == 100
    assert bbox.y == 50
    assert bbox.width == 200
    assert bbox.height == 100
    
    # 测试负坐标（应该被Pydantic验证拒绝）
    with pytest.raises(Exception):
        BoundingBox(x=-10, y=50, width=200, height=100)
    
    # 测试零宽度（应该被Pydantic验证拒绝）
    with pytest.raises(Exception):
        BoundingBox(x=100, y=50, width=0, height=100)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
