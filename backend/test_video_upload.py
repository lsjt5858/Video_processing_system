"""
测试视频上传功能
"""
import pytest
import asyncio
import io
from pathlib import Path
from fastapi import UploadFile

# 添加app目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.video_import import (
    validate_video_format,
    validate_file_size,
    upload_single_video,
    upload_batch_videos,
    FileSizeExceededError,
    UnsupportedFormatError,
    MAX_FILE_SIZE,
    MAX_BATCH_SIZE
)


def test_validate_video_format_supported():
    """测试支持的视频格式验证"""
    # 测试支持的格式
    assert validate_video_format("video.mp4") == "mp4"
    assert validate_video_format("video.avi") == "avi"
    assert validate_video_format("video.mov") == "mov"
    assert validate_video_format("video.mkv") == "mkv"
    
    # 测试大小写不敏感
    assert validate_video_format("video.MP4") == "mp4"
    assert validate_video_format("video.AVI") == "avi"


def test_validate_video_format_unsupported():
    """测试不支持的视频格式"""
    with pytest.raises(UnsupportedFormatError):
        validate_video_format("video.wmv")
    
    with pytest.raises(UnsupportedFormatError):
        validate_video_format("video.flv")
    
    with pytest.raises(UnsupportedFormatError):
        validate_video_format("document.pdf")


def test_validate_file_size_within_limit():
    """测试文件大小在限制内"""
    # 1GB - 应该通过
    validate_file_size(1 * 1024 * 1024 * 1024)
    
    # 4.9GB - 应该通过
    validate_file_size(int(4.9 * 1024 * 1024 * 1024))
    
    # 5GB - 边界值，应该通过
    validate_file_size(5 * 1024 * 1024 * 1024)


def test_validate_file_size_exceeds_limit():
    """测试文件大小超过限制"""
    # 5.1GB - 应该失败
    with pytest.raises(FileSizeExceededError):
        validate_file_size(int(5.1 * 1024 * 1024 * 1024))
    
    # 10GB - 应该失败
    with pytest.raises(FileSizeExceededError):
        validate_file_size(10 * 1024 * 1024 * 1024)


def create_mock_upload_file(filename: str, content: bytes) -> UploadFile:
    """创建模拟的UploadFile对象"""
    file_obj = io.BytesIO(content)
    return UploadFile(filename=filename, file=file_obj)


@pytest.mark.asyncio
async def test_upload_single_video_success():
    """测试单个视频上传成功"""
    # 使用真实的测试视频文件
    test_video_path = Path(__file__).parent / "test_videos" / "test_video.mp4"
    
    if not test_video_path.exists():
        pytest.skip("测试视频不存在，跳过测试")
    
    # 读取测试视频文件
    with open(test_video_path, "rb") as f:
        content = f.read()
    
    upload_file = create_mock_upload_file("test_video.mp4", content)
    
    try:
        result = await upload_single_video(upload_file, user_id="test_user")
        
        # 验证返回结果
        assert result.video_id is not None
        assert result.metadata.format.value == "mp4"
        assert result.metadata.file_size == len(content)
        assert result.import_source == "local"
        assert Path(result.storage_path).exists()
        
        # 验证元数据已正确提取
        assert result.metadata.resolution[0] > 0
        assert result.metadata.resolution[1] > 0
        assert result.metadata.duration > 0
        assert result.metadata.framerate > 0
        
        # 清理测试文件
        Path(result.storage_path).unlink()
        
    except Exception as e:
        pytest.fail(f"上传失败: {str(e)}")


@pytest.mark.asyncio
async def test_upload_single_video_unsupported_format():
    """测试上传不支持的格式"""
    content = b"fake content"
    upload_file = create_mock_upload_file("test_video.wmv", content)
    
    with pytest.raises(UnsupportedFormatError):
        await upload_single_video(upload_file, user_id="test_user")


@pytest.mark.asyncio
async def test_upload_batch_videos_success():
    """测试批量上传成功"""
    # 使用真实的测试视频文件
    test_video_path = Path(__file__).parent / "test_videos" / "test_video.mp4"
    
    if not test_video_path.exists():
        pytest.skip("测试视频不存在，跳过测试")
    
    # 读取测试视频文件
    with open(test_video_path, "rb") as f:
        content = f.read()
    
    # 创建3个测试文件（使用相同的真实视频内容）
    files = [
        create_mock_upload_file(f"test_video_{i}.mp4", content)
        for i in range(3)
    ]
    
    try:
        results = await upload_batch_videos(files, user_id="test_user")
        
        # 验证结果
        assert results["total"] == 3
        assert results["success_count"] == 3
        assert results["failed_count"] == 0
        assert len(results["successful"]) == 3
        
        # 清理测试文件
        for item in results["successful"]:
            Path(item["storage_path"]).unlink()
            
    except Exception as e:
        pytest.fail(f"批量上传失败: {str(e)}")


@pytest.mark.asyncio
async def test_upload_batch_videos_mixed_results():
    """测试批量上传混合结果（部分成功，部分失败）"""
    # 使用真实的测试视频文件
    test_video_path = Path(__file__).parent / "test_videos" / "test_video.mp4"
    
    if not test_video_path.exists():
        pytest.skip("测试视频不存在，跳过测试")
    
    # 读取测试视频文件
    with open(test_video_path, "rb") as f:
        valid_content = f.read()
    
    # 创建混合文件：2个有效，1个无效格式
    files = [
        create_mock_upload_file("test_video_1.mp4", valid_content),
        create_mock_upload_file("test_video_2.wmv", b"content" * 100),  # 不支持的格式
        create_mock_upload_file("test_video_3.avi", valid_content),
    ]
    
    try:
        results = await upload_batch_videos(files, user_id="test_user")
        
        # 验证结果
        assert results["total"] == 3
        assert results["success_count"] == 2
        assert results["failed_count"] == 1
        assert len(results["successful"]) == 2
        assert len(results["failed"]) == 1
        
        # 验证失败的文件
        assert results["failed"][0]["filename"] == "test_video_2.wmv"
        
        # 清理测试文件
        for item in results["successful"]:
            Path(item["storage_path"]).unlink()
            
    except Exception as e:
        pytest.fail(f"批量上传失败: {str(e)}")


def test_format_validation_property():
    """
    属性测试：验证所有支持的格式都能通过验证
    Feature: video-recreation-platform, Property 1: 视频格式验证
    """
    supported_formats = ["mp4", "avi", "mov", "mkv"]
    
    for fmt in supported_formats:
        # 测试小写
        result = validate_video_format(f"video.{fmt}")
        assert result == fmt
        
        # 测试大写
        result = validate_video_format(f"video.{fmt.upper()}")
        assert result == fmt


def test_unsupported_format_rejection_property():
    """
    属性测试：验证不支持的格式都会被拒绝
    Feature: video-recreation-platform, Property 1: 视频格式验证
    """
    unsupported_formats = ["wmv", "flv", "webm", "ogv", "3gp", "txt", "pdf"]
    
    for fmt in unsupported_formats:
        with pytest.raises(UnsupportedFormatError):
            validate_video_format(f"video.{fmt}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
