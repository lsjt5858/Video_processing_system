"""
快速验证模型定义是否正确
"""

from app.models import (
    VideoFormat, ProcessingMode, TaskStatus,
    BoundingBox, VideoMetadata, WatermarkRegion, ProcessingTask
)
from datetime import datetime


def test_bounding_box():
    """测试BoundingBox模型"""
    bbox = BoundingBox(x=100, y=50, width=200, height=100)
    assert bbox.x == 100
    assert bbox.y == 50
    assert bbox.width == 200
    assert bbox.height == 100
    print("✓ BoundingBox 模型验证通过")


def test_video_metadata():
    """测试VideoMetadata模型"""
    metadata = VideoMetadata(
        video_id="vid_123",
        format=VideoFormat.MP4,
        resolution=(1920, 1080),
        duration=120.5,
        codec="h264",
        framerate=30.0,
        bitrate=5000000,
        file_size=104857600
    )
    assert metadata.video_id == "vid_123"
    assert metadata.format == VideoFormat.MP4
    assert metadata.resolution == (1920, 1080)
    assert metadata.duration == 120.5
    print("✓ VideoMetadata 模型验证通过")


def test_watermark_region():
    """测试WatermarkRegion模型"""
    bbox = BoundingBox(x=100, y=50, width=200, height=100)
    region = WatermarkRegion(
        region_id="reg_123",
        video_id="vid_123",
        bbox=bbox,
        start_time=0.0,
        end_time=120.5,
        confidence=0.95,
        watermark_type="corner",
        detection_method="auto"
    )
    assert region.region_id == "reg_123"
    assert region.video_id == "vid_123"
    assert region.bbox.x == 100
    assert region.confidence == 0.95
    assert region.watermark_type == "corner"
    print("✓ WatermarkRegion 模型验证通过")


def test_processing_task():
    """测试ProcessingTask模型"""
    task = ProcessingTask(
        task_id="task_123",
        user_id="user_123",
        video_id="vid_123",
        task_type="removal",
        status=TaskStatus.PENDING,
        parameters={"mode": "crop_reconstruct"}
    )
    assert task.task_id == "task_123"
    assert task.user_id == "user_123"
    assert task.status == TaskStatus.PENDING
    assert task.task_type == "removal"
    print("✓ ProcessingTask 模型验证通过")


def test_validation_errors():
    """测试数据验证"""
    # 测试负数宽度应该失败
    try:
        BoundingBox(x=100, y=50, width=-200, height=100)
        assert False, "应该抛出验证错误"
    except Exception:
        print("✓ BoundingBox 负数验证通过")
    
    # 测试无效的水印类型应该失败
    try:
        bbox = BoundingBox(x=100, y=50, width=200, height=100)
        WatermarkRegion(
            region_id="reg_123",
            video_id="vid_123",
            bbox=bbox,
            start_time=0.0,
            end_time=120.5,
            confidence=0.95,
            watermark_type="invalid_type",
            detection_method="auto"
        )
        assert False, "应该抛出验证错误"
    except Exception:
        print("✓ WatermarkRegion 类型验证通过")
    
    # 测试结束时间小于开始时间应该失败
    try:
        bbox = BoundingBox(x=100, y=50, width=200, height=100)
        WatermarkRegion(
            region_id="reg_123",
            video_id="vid_123",
            bbox=bbox,
            start_time=120.5,
            end_time=0.0,
            confidence=0.95,
            watermark_type="corner",
            detection_method="auto"
        )
        assert False, "应该抛出验证错误"
    except Exception:
        print("✓ WatermarkRegion 时间范围验证通过")


if __name__ == "__main__":
    print("开始验证数据模型...")
    print()
    
    test_bounding_box()
    test_video_metadata()
    test_watermark_region()
    test_processing_task()
    test_validation_errors()
    
    print()
    print("所有模型验证通过！✓")
