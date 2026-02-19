"""
简单的视频上传功能测试（不依赖数据库）
"""
import pytest
from pathlib import Path

# 添加app目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.video_import import (
    validate_video_format,
    validate_file_size,
    FileSizeExceededError,
    UnsupportedFormatError,
    MAX_FILE_SIZE,
    SUPPORTED_FORMATS
)


class TestVideoFormatValidation:
    """测试视频格式验证"""
    
    def test_supported_formats(self):
        """测试支持的视频格式"""
        assert validate_video_format("video.mp4") == "mp4"
        assert validate_video_format("video.avi") == "avi"
        assert validate_video_format("video.mov") == "mov"
        assert validate_video_format("video.mkv") == "mkv"
    
    def test_case_insensitive(self):
        """测试格式验证大小写不敏感"""
        assert validate_video_format("video.MP4") == "mp4"
        assert validate_video_format("video.AVI") == "avi"
        assert validate_video_format("VIDEO.MOV") == "mov"
        assert validate_video_format("Video.MKV") == "mkv"
    
    def test_unsupported_formats(self):
        """测试不支持的格式被拒绝"""
        unsupported = ["wmv", "flv", "webm", "ogv", "3gp"]
        for fmt in unsupported:
            with pytest.raises(UnsupportedFormatError):
                validate_video_format(f"video.{fmt}")
    
    def test_non_video_formats(self):
        """测试非视频格式被拒绝"""
        with pytest.raises(UnsupportedFormatError):
            validate_video_format("document.pdf")
        with pytest.raises(UnsupportedFormatError):
            validate_video_format("image.jpg")
        with pytest.raises(UnsupportedFormatError):
            validate_video_format("audio.mp3")


class TestFileSizeValidation:
    """测试文件大小验证"""
    
    def test_small_file(self):
        """测试小文件通过验证"""
        # 1MB
        validate_file_size(1 * 1024 * 1024)
        # 100MB
        validate_file_size(100 * 1024 * 1024)
        # 1GB
        validate_file_size(1 * 1024 * 1024 * 1024)
    
    def test_boundary_values(self):
        """测试边界值"""
        # 4.9GB - 应该通过
        validate_file_size(int(4.9 * 1024 * 1024 * 1024))
        
        # 5GB - 边界值，应该通过
        validate_file_size(5 * 1024 * 1024 * 1024)
    
    def test_exceeds_limit(self):
        """测试超过限制的文件"""
        # 5.1GB - 应该失败
        with pytest.raises(FileSizeExceededError):
            validate_file_size(int(5.1 * 1024 * 1024 * 1024))
        
        # 10GB - 应该失败
        with pytest.raises(FileSizeExceededError):
            validate_file_size(10 * 1024 * 1024 * 1024)
        
        # 100GB - 应该失败
        with pytest.raises(FileSizeExceededError):
            validate_file_size(100 * 1024 * 1024 * 1024)


class TestPropertyBasedValidation:
    """
    基于属性的测试
    Feature: video-recreation-platform, Property 1: 视频格式验证
    """
    
    def test_all_supported_formats_accepted(self):
        """属性：所有支持的格式都应该被接受"""
        supported_formats = ["mp4", "avi", "mov", "mkv"]
        
        for fmt in supported_formats:
            # 测试小写
            result = validate_video_format(f"video.{fmt}")
            assert result == fmt, f"格式 {fmt} 应该被接受"
            
            # 测试大写
            result = validate_video_format(f"video.{fmt.upper()}")
            assert result == fmt, f"格式 {fmt.upper()} 应该被接受"
            
            # 测试混合大小写
            result = validate_video_format(f"video.{fmt.capitalize()}")
            assert result == fmt, f"格式 {fmt.capitalize()} 应该被接受"
    
    def test_unsupported_formats_rejected(self):
        """属性：所有不支持的格式都应该被拒绝"""
        unsupported_formats = [
            "wmv", "flv", "webm", "ogv", "3gp",
            "txt", "pdf", "jpg", "png", "mp3", "wav"
        ]
        
        for fmt in unsupported_formats:
            with pytest.raises(UnsupportedFormatError):
                validate_video_format(f"video.{fmt}")
    
    def test_file_size_boundary(self):
        """属性：文件大小边界测试"""
        max_size = 5 * 1024 * 1024 * 1024  # 5GB
        
        # 测试边界以下的值
        test_sizes = [
            max_size - 1,
            max_size - 1024,
            max_size - 1024 * 1024,
            max_size - 1024 * 1024 * 1024,
        ]
        
        for size in test_sizes:
            validate_file_size(size)  # 应该通过
        
        # 测试边界值
        validate_file_size(max_size)  # 应该通过
        
        # 测试超过边界的值
        over_sizes = [
            max_size + 1,
            max_size + 1024,
            max_size + 1024 * 1024,
            max_size + 1024 * 1024 * 1024,
        ]
        
        for size in over_sizes:
            with pytest.raises(FileSizeExceededError):
                validate_file_size(size)


class TestConstants:
    """测试常量配置"""
    
    def test_max_file_size(self):
        """验证最大文件大小配置"""
        assert MAX_FILE_SIZE == 5 * 1024 * 1024 * 1024  # 5GB
    
    def test_supported_formats_set(self):
        """验证支持的格式集合"""
        expected = {".mp4", ".avi", ".mov", ".mkv"}
        assert SUPPORTED_FORMATS == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
