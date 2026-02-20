"""
错误处理测试

测试新的错误处理机制
"""

import pytest
from pathlib import Path
from app.errors import (
    FileSizeExceededError,
    UnsupportedFormatError,
    InvalidUrlError,
    VideoNotAccessibleError,
    CorruptedVideoError,
    MetadataExtractionError,
    FFmpegError,
    create_error_response,
    log_error
)
from app.video_import import (
    validate_video_format,
    validate_file_size,
    validate_url,
    MAX_FILE_SIZE
)


def test_file_size_exceeded_error():
    """测试文件大小超限错误"""
    file_size = 6 * 1024 * 1024 * 1024  # 6GB
    error = FileSizeExceededError(file_size, MAX_FILE_SIZE, "test.mp4")
    
    assert error.error_code == "FILE_SIZE_EXCEEDED"
    assert error.status_code == 413
    assert "6.00GB" in error.message
    assert error.details["file_name"] == "test.mp4"
    
    # 测试转换为字典
    error_dict = error.to_dict()
    assert error_dict["error"]["code"] == "FILE_SIZE_EXCEEDED"
    assert "timestamp" in error_dict["error"]


def test_unsupported_format_error():
    """测试不支持的格式错误"""
    error = UnsupportedFormatError(".wmv", ["mp4", "avi", "mov", "mkv"])
    
    assert error.error_code == "UNSUPPORTED_FORMAT"
    assert error.status_code == 415
    assert ".wmv" in error.message
    assert error.details["format"] == ".wmv"
    assert "mp4" in error.details["supported_formats"]


def test_invalid_url_error():
    """测试无效URL错误"""
    error = InvalidUrlError("not-a-url", "URL必须以http://或https://开头")
    
    assert error.error_code == "INVALID_URL"
    assert error.status_code == 400
    assert error.details["url"] == "not-a-url"
    assert "http" in error.details["reason"]


def test_corrupted_video_error():
    """测试视频损坏错误"""
    error = CorruptedVideoError("/path/to/video.mp4", "moov atom not found")
    
    assert error.error_code == "CORRUPTED_VIDEO"
    assert error.status_code == 400
    assert "损坏" in error.message
    assert error.details["video_path"] == "/path/to/video.mp4"


def test_metadata_extraction_error():
    """测试元数据提取错误"""
    error = MetadataExtractionError("/path/to/video.mp4", "FFprobe执行失败")
    
    assert error.error_code == "METADATA_EXTRACTION_ERROR"
    assert error.status_code == 500
    assert "元数据" in error.message


def test_ffmpeg_error():
    """测试FFmpeg错误"""
    error = FFmpegError("ffmpeg -i input.mp4 output.mp4", "Invalid data found", 1)
    
    assert error.error_code == "FFMPEG_ERROR"
    assert error.status_code == 500
    assert error.details["command"] == "ffmpeg -i input.mp4 output.mp4"
    assert error.details["returncode"] == 1


def test_validate_video_format_valid():
    """测试有效的视频格式验证"""
    assert validate_video_format("test.mp4") == "mp4"
    assert validate_video_format("test.MP4") == "mp4"
    assert validate_video_format("test.avi") == "avi"
    assert validate_video_format("test.mov") == "mov"
    assert validate_video_format("test.mkv") == "mkv"


def test_validate_video_format_invalid():
    """测试无效的视频格式验证"""
    with pytest.raises(UnsupportedFormatError) as exc_info:
        validate_video_format("test.wmv")
    
    assert exc_info.value.error_code == "UNSUPPORTED_FORMAT"
    assert ".wmv" in exc_info.value.details["format"]


def test_validate_video_format_empty():
    """测试空文件名验证"""
    with pytest.raises(UnsupportedFormatError):
        validate_video_format("")


def test_validate_file_size_valid():
    """测试有效的文件大小验证"""
    # 4.5GB - 应该通过
    file_size = int(4.5 * 1024 * 1024 * 1024)
    validate_file_size(file_size, "test.mp4")  # 不应该抛出异常


def test_validate_file_size_invalid():
    """测试无效的文件大小验证"""
    # 5.5GB - 应该失败
    file_size = int(5.5 * 1024 * 1024 * 1024)
    
    with pytest.raises(FileSizeExceededError) as exc_info:
        validate_file_size(file_size, "test.mp4")
    
    assert exc_info.value.error_code == "FILE_SIZE_EXCEEDED"
    assert exc_info.value.details["file_size"] == file_size
    assert exc_info.value.details["file_name"] == "test.mp4"


def test_validate_url_valid():
    """测试有效的URL验证"""
    validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    validate_url("http://example.com/video.mp4")


def test_validate_url_empty():
    """测试空URL验证"""
    with pytest.raises(InvalidUrlError) as exc_info:
        validate_url("")
    
    assert "空" in exc_info.value.details["reason"]


def test_validate_url_no_protocol():
    """测试缺少协议的URL验证"""
    with pytest.raises(InvalidUrlError) as exc_info:
        validate_url("www.example.com/video.mp4")
    
    assert "http" in exc_info.value.details["reason"]


def test_validate_url_with_spaces():
    """测试包含空格的URL验证"""
    with pytest.raises(InvalidUrlError) as exc_info:
        validate_url("https://example.com/video file.mp4")
    
    assert "空格" in exc_info.value.details["reason"]


def test_validate_url_too_long():
    """测试过长的URL验证"""
    long_url = "https://example.com/" + "a" * 2100
    
    with pytest.raises(InvalidUrlError) as exc_info:
        validate_url(long_url)
    
    assert "长度" in exc_info.value.details["reason"]


def test_create_error_response_with_video_processing_error():
    """测试创建视频处理错误响应"""
    error = FileSizeExceededError(6 * 1024 * 1024 * 1024, MAX_FILE_SIZE, "test.mp4")
    response = create_error_response(error, "req_123")
    
    assert response["error"]["code"] == "FILE_SIZE_EXCEEDED"
    assert response["error"]["request_id"] == "req_123"
    assert "timestamp" in response["error"]


def test_create_error_response_with_generic_error():
    """测试创建通用错误响应"""
    error = ValueError("Something went wrong")
    response = create_error_response(error)
    
    assert response["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response["error"]["message"] == "服务器内部错误"
    assert response["error"]["details"]["error_type"] == "ValueError"


def test_log_error():
    """测试错误日志记录"""
    error = FileSizeExceededError(6 * 1024 * 1024 * 1024, MAX_FILE_SIZE, "test.mp4")
    
    # 应该不抛出异常
    log_error(error, {"operation": "upload", "user_id": "test_user"})
    
    # 测试通用错误
    generic_error = Exception("Test error")
    log_error(generic_error, {"operation": "test"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
