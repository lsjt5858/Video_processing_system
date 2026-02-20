"""
集成测试：手动水印标记功能

使用真实视频文件测试完整的手动标记流程
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
    extract_frames_for_preview,
    mark_watermark_regions,
    validate_bounding_box
)
from app.database import AsyncSessionLocal, init_db
from app import crud


@pytest.mark.asyncio
async def test_extract_frames_for_preview_with_real_video():
    """测试使用真实视频提取预览帧"""
    # 查找测试视频文件
    test_video_path = Path(__file__).parent.parent / "uploads"
    
    # 查找第一个视频文件
    video_files = list(test_video_path.glob("*.mp4"))
    if not video_files:
        pytest.skip("没有找到测试视频文件")
    
    video_path = str(video_files[0])
    video_id = video_files[0].stem
    
    # 提取预览帧
    frames = await extract_frames_for_preview(video_path, video_id, num_frames=5)
    
    # 验证结果
    assert len(frames) > 0
    assert len(frames) <= 5
    
    for frame in frames:
        assert "frame_index" in frame
        assert "timestamp" in frame
        assert "thumbnail_url" in frame
        assert frame["frame_index"] >= 0
        assert frame["timestamp"] >= 0
        assert frame["thumbnail_url"].startswith("/thumbnails/")
    
    print(f"\n成功提取 {len(frames)} 个预览帧")
    for frame in frames:
        print(f"  帧 {frame['frame_index']}: 时间戳 {frame['timestamp']}s, URL: {frame['thumbnail_url']}")


@pytest.mark.asyncio
async def test_mark_watermark_regions_with_real_video():
    """测试使用真实视频标记水印区域"""
    # 初始化数据库
    await init_db()
    
    # 查找测试视频文件
    test_video_path = Path(__file__).parent.parent / "uploads"
    video_files = list(test_video_path.glob("*.mp4"))
    
    if not video_files:
        pytest.skip("没有找到测试视频文件")
    
    video_path = str(video_files[0])
    video_id = f"test_video_{video_files[0].stem}"
    
    async with AsyncSessionLocal() as db_session:
        try:
            # 首先创建视频记录
            video = await crud.create_video(
                db=db_session,
                video_id=video_id,
                user_id="test_user",
                format="mp4",
                resolution_width=1920,
                resolution_height=1080,
                duration=10.0,
                codec="h264",
                framerate=30.0,
                bitrate=5000000,
                file_size=1048576,
                storage_path=video_path,
                import_source="local"
            )
            
            # 定义多个水印区域
            bounding_boxes = [
                {
                    "x": 100,
                    "y": 50,
                    "width": 200,
                    "height": 100,
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "watermark_type": "corner"
                },
                {
                    "x": 1600,
                    "y": 900,
                    "width": 300,
                    "height": 150,
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "watermark_type": "logo"
                },
                {
                    "x": 800,
                    "y": 950,
                    "width": 320,
                    "height": 80,
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "watermark_type": "subtitle"
                }
            ]
            
            # 标记水印区域
            regions = await mark_watermark_regions(
                db=db_session,
                video_id=video_id,
                video_path=video_path,
                bounding_boxes=bounding_boxes
            )
            
            await db_session.commit()
            
            # 验证结果
            assert len(regions) == 3
            
            for i, region in enumerate(regions):
                assert region.video_id == video_id
                assert region.detection_method == "manual"
                assert region.confidence == 1.0
                assert region.bbox_x == bounding_boxes[i]["x"]
                assert region.bbox_y == bounding_boxes[i]["y"]
                assert region.bbox_width == bounding_boxes[i]["width"]
                assert region.bbox_height == bounding_boxes[i]["height"]
                assert region.watermark_type == bounding_boxes[i]["watermark_type"]
            
            print(f"\n成功标记 {len(regions)} 个水印区域")
            for region in regions:
                print(f"  区域 {region.region_id}: 类型={region.watermark_type}, "
                      f"位置=({region.bbox_x}, {region.bbox_y}), "
                      f"大小={region.bbox_width}x{region.bbox_height}")
            
            # 验证可以从数据库读取
            saved_regions = await crud.get_watermark_regions_by_video(db_session, video_id)
            assert len(saved_regions) == 3
            
        finally:
            await db_session.rollback()


@pytest.mark.asyncio
async def test_mark_invalid_bounding_box():
    """测试标记无效的边界框"""
    # 初始化数据库
    await init_db()
    
    # 查找测试视频文件
    test_video_path = Path(__file__).parent.parent / "uploads"
    video_files = list(test_video_path.glob("*.mp4"))
    
    if not video_files:
        pytest.skip("没有找到测试视频文件")
    
    video_path = str(video_files[0])
    video_id = f"test_video_invalid_{video_files[0].stem}"
    
    async with AsyncSessionLocal() as db_session:
        try:
            # 创建视频记录
            video = await crud.create_video(
                db=db_session,
                video_id=video_id,
                user_id="test_user",
                format="mp4",
                resolution_width=1920,
                resolution_height=1080,
                duration=10.0,
                codec="h264",
                framerate=30.0,
                bitrate=5000000,
                file_size=1048576,
                storage_path=video_path,
                import_source="local"
            )
            
            # 定义超出视频范围的边界框
            bounding_boxes = [
                {
                    "x": 1800,
                    "y": 50,
                    "width": 200,  # 1800 + 200 = 2000 > 1920
                    "height": 100,
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "watermark_type": "corner"
                }
            ]
            
            # 应该抛出ValueError
            with pytest.raises(ValueError, match="无效的边界框"):
                await mark_watermark_regions(
                    db=db_session,
                    video_id=video_id,
                    video_path=video_path,
                    bounding_boxes=bounding_boxes
                )
            
            print("\n成功检测到无效的边界框")
            
        finally:
            await db_session.rollback()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
