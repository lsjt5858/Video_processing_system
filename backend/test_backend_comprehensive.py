"""
综合后端功能测试

Task 10.1: 后端功能测试
- 测试视频上传（不同格式、大小）
- 测试批量上传（并发控制）
- 测试URL下载（不同视频网站）
- 测试水印标记（单个、多个区域）
- 测试水印去除（不同裁剪参数）
- 测试批量处理（多个视频）
"""

import pytest
import asyncio
import io
import uuid
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# 添加app目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.video_import import (
    validate_video_format,
    validate_file_size,
    upload_single_video,
    upload_batch_videos,
    download_video_from_url,
    FileSizeExceededError,
    UnsupportedFormatError,
    MAX_FILE_SIZE
)
from app.watermark_detection import (
    validate_bounding_box,
    save_manual_watermark_region,
    mark_watermark_regions
)
from app.watermark_removal import WatermarkRemovalEngine
from app.models import (
    BoundingBox,
    WatermarkRegion,
    ProcessingMode,
    VideoFormat
)
from fastapi import UploadFile


# ============================================================================
# 测试辅助函数
# ============================================================================

def create_mock_upload_file(filename: str, content: bytes) -> UploadFile:
    """创建模拟的UploadFile对象"""
    file_obj = io.BytesIO(content)
    return UploadFile(filename=filename, file=file_obj)


def get_test_video_content() -> bytes:
    """获取测试视频内容"""
    test_video_path = Path(__file__).parent / "test_videos" / "test_video.mp4"
    if not test_video_path.exists():
        pytest.skip("测试视频不存在，跳过测试")
    with open(test_video_path, "rb") as f:
        return f.read()


def create_watermark_region(
    region_id: str,
    video_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    watermark_type: str = "corner"
) -> WatermarkRegion:
    """创建水印区域对象"""
    return WatermarkRegion(
        region_id=region_id,
        video_id=video_id,
        bbox=BoundingBox(x=x, y=y, width=width, height=height),
        start_time=0.0,
        end_time=10.0,
        confidence=0.95,
        watermark_type=watermark_type,
        detection_method="manual"
    )


# ============================================================================
# 1. 视频上传测试（不同格式、大小）
# ============================================================================

class TestVideoUploadFormats:
    """测试视频上传 - 不同格式"""
    
    def test_supported_formats(self):
        """测试支持的视频格式：MP4, AVI, MOV, MKV"""
        supported_formats = ["mp4", "avi", "mov", "mkv"]
        
        for fmt in supported_formats:
            # 测试小写
            result = validate_video_format(f"video.{fmt}")
            assert result == fmt, f"格式 {fmt} 应该被支持"
            
            # 测试大写
            result = validate_video_format(f"video.{fmt.upper()}")
            assert result == fmt, f"格式 {fmt.upper()} 应该被支持（大小写不敏感）"
    
    def test_unsupported_formats(self):
        """测试不支持的视频格式"""
        unsupported_formats = ["wmv", "flv", "webm", "ogv", "3gp", "txt", "pdf"]
        
        for fmt in unsupported_formats:
            with pytest.raises(UnsupportedFormatError):
                validate_video_format(f"video.{fmt}")
    
    @pytest.mark.asyncio
    async def test_upload_mp4_format(self):
        """测试上传MP4格式视频"""
        content = get_test_video_content()
        upload_file = create_mock_upload_file("test.mp4", content)
        
        result = await upload_single_video(upload_file, user_id="test_user")
        
        assert result.video_id is not None
        assert result.metadata.format == VideoFormat.MP4
        assert Path(result.storage_path).exists()
        
        # 清理
        Path(result.storage_path).unlink()
    
    @pytest.mark.asyncio
    async def test_upload_avi_format(self):
        """测试上传AVI格式视频"""
        content = get_test_video_content()
        upload_file = create_mock_upload_file("test.avi", content)
        
        result = await upload_single_video(upload_file, user_id="test_user")
        
        assert result.video_id is not None
        assert result.metadata.format == VideoFormat.AVI
        assert Path(result.storage_path).exists()
        
        # 清理
        Path(result.storage_path).unlink()


class TestVideoUploadSizes:
    """测试视频上传 - 不同大小"""
    
    def test_file_size_within_limit(self):
        """测试文件大小在限制内（5GB以下）"""
        # 1GB - 应该通过
        validate_file_size(1 * 1024 * 1024 * 1024)
        
        # 2.5GB - 应该通过
        validate_file_size(int(2.5 * 1024 * 1024 * 1024))
        
        # 4.9GB - 应该通过
        validate_file_size(int(4.9 * 1024 * 1024 * 1024))
        
        # 5GB - 边界值，应该通过
        validate_file_size(5 * 1024 * 1024 * 1024)
    
    def test_file_size_exceeds_limit(self):
        """测试文件大小超过限制（5GB以上）"""
        # 5.1GB - 应该失败
        with pytest.raises(FileSizeExceededError):
            validate_file_size(int(5.1 * 1024 * 1024 * 1024))
        
        # 10GB - 应该失败
        with pytest.raises(FileSizeExceededError):
            validate_file_size(10 * 1024 * 1024 * 1024)
        
        # 100GB - 应该失败
        with pytest.raises(FileSizeExceededError):
            validate_file_size(100 * 1024 * 1024 * 1024)
    
    def test_file_size_boundary(self):
        """测试文件大小边界值"""
        # 正好5GB
        validate_file_size(MAX_FILE_SIZE)
        
        # 5GB + 1字节 - 应该失败
        with pytest.raises(FileSizeExceededError):
            validate_file_size(MAX_FILE_SIZE + 1)


# ============================================================================
# 2. 批量上传测试（并发控制）
# ============================================================================

class TestBatchUploadConcurrency:
    """测试批量上传 - 并发控制"""
    
    @pytest.mark.asyncio
    async def test_batch_upload_concurrent_limit(self):
        """测试批量上传的并发限制（最多5个并行）"""
        content = get_test_video_content()
        
        # 创建10个文件
        files = [
            create_mock_upload_file(f"test_{i}.mp4", content)
            for i in range(10)
        ]
        
        # 跟踪并发数
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()
        
        async def mock_websocket_callback(client_id: str, message: dict):
            nonlocal concurrent_count, max_concurrent
            
            async with lock:
                if message.get("status") == "uploading":
                    concurrent_count += 1
                    max_concurrent = max(max_concurrent, concurrent_count)
                elif message.get("status") in ["completed", "failed"]:
                    concurrent_count -= 1
        
        # 执行批量上传
        result = await upload_batch_videos(
            files=files,
            user_id="test_user",
            websocket_callback=mock_websocket_callback,
            client_id="test_client"
        )
        
        # 验证结果
        assert result["total"] == 10
        assert result["success_count"] + result["failed_count"] == 10
        
        # 验证并发限制（最多5个）
        assert max_concurrent <= 5, f"并发数 {max_concurrent} 超过限制 5"
        
        # 清理测试文件
        for item in result["successful"]:
            storage_path = Path(item["storage_path"])
            if storage_path.exists():
                storage_path.unlink()
    
    @pytest.mark.asyncio
    async def test_batch_upload_progress_tracking(self):
        """测试批量上传的进度跟踪"""
        content = get_test_video_content()
        
        # 创建3个文件
        files = [
            create_mock_upload_file(f"test_{i}.mp4", content)
            for i in range(3)
        ]
        
        # 跟踪进度消息
        progress_messages = []
        
        async def mock_websocket_callback(client_id: str, message: dict):
            progress_messages.append(message)
        
        # 执行批量上传
        result = await upload_batch_videos(
            files=files,
            user_id="test_user",
            websocket_callback=mock_websocket_callback,
            client_id="test_client"
        )
        
        # 验证结果
        assert result["total"] == 3
        assert result["success_count"] == 3
        
        # 验证进度消息
        uploading_messages = [m for m in progress_messages if m.get("status") == "uploading"]
        completed_messages = [m for m in progress_messages if m.get("status") == "completed"]
        
        assert len(uploading_messages) == 3, "应该有3个上传中消息"
        assert len(completed_messages) == 3, "应该有3个完成消息"
        
        # 验证每个消息包含必要字段
        for msg in uploading_messages:
            assert "file_index" in msg
            assert "filename" in msg
            assert "progress" in msg
            assert msg["type"] == "batch_upload_progress"
        
        # 清理测试文件
        for item in result["successful"]:
            storage_path = Path(item["storage_path"])
            if storage_path.exists():
                storage_path.unlink()
    
    @pytest.mark.asyncio
    async def test_batch_upload_error_isolation(self):
        """测试批量上传的错误隔离（单个文件失败不影响其他文件）"""
        content = get_test_video_content()
        
        # 创建混合文件：2个有效，1个无效格式
        files = [
            create_mock_upload_file("test1.mp4", content),
            create_mock_upload_file("test2.wmv", b"fake content"),  # 不支持的格式
            create_mock_upload_file("test3.avi", content),
        ]
        
        # 执行批量上传
        result = await upload_batch_videos(
            files=files,
            user_id="test_user"
        )
        
        # 验证结果
        assert result["total"] == 3
        assert result["success_count"] == 2, "应该有2个文件成功"
        assert result["failed_count"] == 1, "应该有1个文件失败"
        
        # 验证成功的文件
        assert len(result["successful"]) == 2
        successful_filenames = [item["filename"] for item in result["successful"]]
        assert "test1.mp4" in successful_filenames
        assert "test3.avi" in successful_filenames
        
        # 验证失败的文件
        assert len(result["failed"]) == 1
        assert result["failed"][0]["filename"] == "test2.wmv"
        assert "error" in result["failed"][0]
        
        # 清理测试文件
        for item in result["successful"]:
            storage_path = Path(item["storage_path"])
            if storage_path.exists():
                storage_path.unlink()


# ============================================================================
# 3. URL下载测试（不同视频网站）
# ============================================================================

class TestURLDownload:
    """测试URL下载 - 不同视频网站"""
    
    @pytest.mark.asyncio
    async def test_invalid_url_error(self):
        """测试无效URL错误处理"""
        from app.video_import import InvalidUrlError, VideoNotAccessibleError
        
        invalid_urls = [
            "not_a_valid_url",
            "javascript:alert('xss')",
            ""
        ]
        
        for url in invalid_urls:
            with pytest.raises((InvalidUrlError, VideoNotAccessibleError)):
                await download_video_from_url(url)
    
    @pytest.mark.asyncio
    async def test_unsupported_url_error(self):
        """测试不支持的URL错误处理"""
        from app.video_import import InvalidUrlError, VideoNotAccessibleError
        
        # 使用一个不支持的URL格式
        unsupported_url = "http://example.com/not_a_video"
        
        with pytest.raises((InvalidUrlError, VideoNotAccessibleError)):
            await download_video_from_url(unsupported_url)
    
    @pytest.mark.skip(reason="需要网络连接和真实视频URL")
    @pytest.mark.asyncio
    async def test_download_youtube_video(self):
        """测试下载YouTube视频"""
        # 注意：此测试需要网络连接和有效的YouTube URL
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        result = await download_video_from_url(test_url)
        
        assert result.video_id is not None
        assert result.metadata is not None
        assert result.storage_path is not None
        assert result.import_source == "url"
        
        # 清理下载的文件
        if Path(result.storage_path).exists():
            Path(result.storage_path).unlink()
    
    @pytest.mark.skip(reason="需要网络连接和真实视频URL")
    @pytest.mark.asyncio
    async def test_download_bilibili_video(self):
        """测试下载Bilibili视频"""
        # 注意：此测试需要网络连接和有效的Bilibili URL
        test_url = "https://www.bilibili.com/video/BVtest"
        
        result = await download_video_from_url(test_url)
        
        assert result.video_id is not None
        assert result.import_source == "url"
        
        # 清理下载的文件
        if Path(result.storage_path).exists():
            Path(result.storage_path).unlink()


# ============================================================================
# 4. 水印标记测试（单个、多个区域）
# ============================================================================

class TestWatermarkMarking:
    """测试水印标记 - 单个和多个区域"""
    
    @pytest.mark.asyncio
    async def test_mark_single_watermark_region(self):
        """测试标记单个水印区域"""
        bbox = BoundingBox(x=100, y=50, width=200, height=100)
        video_width = 1920
        video_height = 1080
        
        # 验证边界框有效
        result = await validate_bounding_box(bbox, video_width, video_height)
        assert result is True, "单个水印区域应该有效"
    
    @pytest.mark.asyncio
    async def test_mark_multiple_watermark_regions(self):
        """测试标记多个水印区域"""
        # 创建多个水印区域
        regions = [
            BoundingBox(x=100, y=50, width=200, height=100),  # 左上角
            BoundingBox(x=1600, y=50, width=200, height=100),  # 右上角
            BoundingBox(x=800, y=950, width=300, height=100),  # 底部中央
        ]
        
        video_width = 1920
        video_height = 1080
        
        # 验证所有区域都有效
        for bbox in regions:
            result = await validate_bounding_box(bbox, video_width, video_height)
            assert result is True, f"水印区域 {bbox} 应该有效"
    
    @pytest.mark.asyncio
    async def test_mark_corner_watermarks(self):
        """测试标记四个角的水印"""
        video_width = 1920
        video_height = 1080
        
        # 四个角的水印
        corners = [
            BoundingBox(x=0, y=0, width=150, height=80),  # 左上
            BoundingBox(x=1770, y=0, width=150, height=80),  # 右上
            BoundingBox(x=0, y=1000, width=150, height=80),  # 左下
            BoundingBox(x=1770, y=1000, width=150, height=80),  # 右下
        ]
        
        for bbox in corners:
            result = await validate_bounding_box(bbox, video_width, video_height)
            assert result is True, f"角落水印 {bbox} 应该有效"
    
    @pytest.mark.asyncio
    async def test_mark_invalid_watermark_region(self):
        """测试标记无效的水印区域"""
        video_width = 1920
        video_height = 1080
        
        # 超出视频边界的区域
        invalid_regions = [
            BoundingBox(x=1800, y=50, width=200, height=100),  # 超出右边界
            BoundingBox(x=100, y=1000, width=200, height=100),  # 超出下边界
            BoundingBox(x=2000, y=50, width=200, height=100),  # 完全超出
        ]
        
        for bbox in invalid_regions:
            result = await validate_bounding_box(bbox, video_width, video_height)
            assert result is False, f"无效区域 {bbox} 应该被拒绝"


# ============================================================================
# 5. 水印去除测试（不同裁剪参数）
# ============================================================================

class TestWatermarkRemoval:
    """测试水印去除 - 不同裁剪参数"""
    
    @pytest.fixture
    def removal_engine(self):
        """创建水印去除引擎"""
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True)
        return WatermarkRemovalEngine(output_dir=str(output_dir))
    
    @pytest.fixture
    def test_video_path(self):
        """获取测试视频路径"""
        video_path = Path(__file__).parent / "test_videos" / "test_video.mp4"
        if not video_path.exists():
            pytest.skip(f"测试视频不存在: {video_path}")
        return str(video_path)
    
    @pytest.fixture
    def video_metadata(self):
        """测试视频元数据"""
        return {
            'resolution_width': 1280,
            'resolution_height': 720,
            'codec': 'h264',
            'framerate': 30.0,
            'duration': 10.0
        }
    
    def test_crop_single_corner_watermark(self, removal_engine):
        """测试裁剪单个角落水印"""
        # 右上角水印
        regions = [
            create_watermark_region("reg1", "vid1", 1200, 0, 80, 60, "corner")
        ]
        result = removal_engine._calculate_optimal_crop(regions, 1280, 720)
        
        assert result['content_integrity'] >= 0.90
        assert result['crop_width'] > 0
        assert result['crop_height'] > 0
    
    def test_crop_bottom_subtitle_watermark(self, removal_engine):
        """测试裁剪底部字幕水印"""
        # 底部小水印
        regions = [
            create_watermark_region("reg1", "vid2", 540, 670, 200, 50, "subtitle")
        ]
        result = removal_engine._calculate_optimal_crop(regions, 1280, 720)
        
        # 应该裁剪掉底部
        assert result['crop_y'] == 0
        assert result['crop_height'] <= 670
        assert result['content_integrity'] >= 0.90
    
    def test_crop_multiple_watermarks(self, removal_engine):
        """测试裁剪多个水印"""
        # 两个水印在同一侧
        regions = [
            create_watermark_region("reg1", "vid3", 0, 0, 80, 50, "corner"),
            create_watermark_region("reg2", "vid3", 0, 670, 80, 50, "corner")
        ]
        result = removal_engine._calculate_optimal_crop(regions, 1280, 720)
        
        # 应该找到能排除两个水印的区域
        assert result['content_integrity'] >= 0.90
        # 两个水印都在左侧，应该裁剪掉左边
        assert result['crop_x'] >= 80
    
    def test_crop_no_watermark(self, removal_engine):
        """测试没有水印时的裁剪（应该返回原始尺寸）"""
        regions = []
        result = removal_engine._calculate_optimal_crop(regions, 1280, 720)
        
        assert result['crop_x'] == 0
        assert result['crop_y'] == 0
        assert result['crop_width'] == 1280
        assert result['crop_height'] == 720
        assert result['content_integrity'] == 1.0
    
    def test_crop_dimensions_are_even(self, removal_engine):
        """测试裁剪尺寸是偶数（视频编码要求）"""
        regions = [
            create_watermark_region("reg1", "vid4", 100, 100, 150, 75, "logo")
        ]
        result = removal_engine._calculate_optimal_crop(regions, 1920, 1080)
        
        # 宽度和高度必须是偶数
        assert result['crop_width'] % 2 == 0, "裁剪宽度必须是偶数"
        assert result['crop_height'] % 2 == 0, "裁剪高度必须是偶数"
    
    def test_crop_execution(self, removal_engine, test_video_path, video_metadata):
        """测试裁剪执行"""
        # 创建一个右下角小水印
        regions = [
            create_watermark_region("reg1", "vid5", 1200, 660, 80, 60, "corner")
        ]
        
        result = removal_engine.crop_reconstruct(
            video_path=test_video_path,
            video_id="vid5",
            regions=regions,
            video_metadata=video_metadata
        )
        
        # 验证返回结果
        assert result.video_id == "vid5"
        assert result.output_video_id.startswith("crop_")
        assert result.processing_mode == ProcessingMode.CROP_RECONSTRUCT
        assert result.processing_duration > 0
        
        # 验证输出文件存在
        assert Path(result.output_path).exists()
        
        # 验证参数
        assert 'crop_x' in result.parameters
        assert 'crop_y' in result.parameters
        assert 'crop_width' in result.parameters
        assert 'crop_height' in result.parameters
        assert result.parameters['content_integrity'] >= 0.90
        
        # 清理
        Path(result.output_path).unlink()


# ============================================================================
# 6. 批量处理测试（多个视频）
# ============================================================================

class TestBatchProcessing:
    """测试批量处理 - 多个视频"""
    
    @pytest.mark.asyncio
    async def test_batch_upload_and_mark(self):
        """测试批量上传和标记"""
        content = get_test_video_content()
        
        # 批量上传3个视频
        files = [
            create_mock_upload_file(f"batch_{i}.mp4", content)
            for i in range(3)
        ]
        
        result = await upload_batch_videos(
            files=files,
            user_id="test_user"
        )
        
        assert result["success_count"] == 3
        assert len(result["successful"]) == 3
        
        # 为每个视频创建水印区域
        # 使用实际视频的分辨率（从元数据中获取）
        for item in result["successful"]:
            # 从上传结果中获取实际的视频分辨率
            video_width = item.get("metadata", {}).get("resolution", [1280, 720])[0]
            video_height = item.get("metadata", {}).get("resolution", [1280, 720])[1]
            
            # 创建一个在视频范围内的水印区域
            bbox = BoundingBox(x=100, y=50, width=100, height=60)
            is_valid = await validate_bounding_box(bbox, video_width, video_height)
            assert is_valid is True
        
        # 清理
        for item in result["successful"]:
            storage_path = Path(item["storage_path"])
            if storage_path.exists():
                storage_path.unlink()
    
    @pytest.mark.asyncio
    async def test_batch_removal_workflow(self):
        """测试批量去除工作流"""
        content = get_test_video_content()
        
        # 1. 批量上传
        files = [
            create_mock_upload_file(f"workflow_{i}.mp4", content)
            for i in range(2)
        ]
        
        upload_result = await upload_batch_videos(
            files=files,
            user_id="test_user"
        )
        
        assert upload_result["success_count"] == 2
        
        # 2. 为每个视频标记水印
        video_ids = [item["video_id"] for item in upload_result["successful"]]
        
        # 3. 批量去除（模拟）
        removal_engine = WatermarkRemovalEngine(output_dir="test_outputs")
        
        for i, item in enumerate(upload_result["successful"]):
            regions = [
                create_watermark_region(f"reg_{i}", item["video_id"], 1200, 50, 80, 60, "corner")
            ]
            
            # 计算裁剪参数
            crop_params = removal_engine._calculate_optimal_crop(regions, 1280, 720)
            assert crop_params['content_integrity'] >= 0.90
        
        # 清理
        for item in upload_result["successful"]:
            storage_path = Path(item["storage_path"])
            if storage_path.exists():
                storage_path.unlink()


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
