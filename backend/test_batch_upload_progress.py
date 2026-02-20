"""
批量上传进度管理测试

测试批量上传的并发控制、进度推送和错误隔离功能
"""
import pytest
import asyncio
import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from typing import List

# 添加app目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.video_import import upload_batch_videos
from app.models import VideoImportResult, VideoMetadata
from fastapi import UploadFile


@pytest.fixture
def test_video_path():
    """获取测试视频文件路径"""
    return Path(__file__).parent / "test_videos" / "test_video.mp4"


def get_real_video_content(test_video_path: Path) -> bytes:
    """读取真实的测试视频内容"""
    if test_video_path.exists():
        with open(test_video_path, "rb") as f:
            return f.read()
    # 如果测试视频不存在，跳过测试
    pytest.skip("测试视频文件不存在")


def create_upload_file(filename: str, content: bytes) -> UploadFile:
    """创建UploadFile对象"""
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content)
    )


@pytest.mark.asyncio
async def test_batch_upload_concurrent_limit(test_video_path):
    """
    测试批量上传的并发限制（最多5个并行）
    
    验证需求: 10.2 - 并行上传最多5个文件
    """
    content = get_real_video_content(test_video_path)
    
    # 创建10个文件
    files = [
        create_upload_file(f"test_{i}.mp4", content)
        for i in range(10)
    ]
    
    # 跟踪并发数
    concurrent_count = 0
    max_concurrent = 0
    lock = asyncio.Lock()
    
    # Mock WebSocket回调来跟踪并发
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
    assert max_concurrent <= 5
    
    # 清理测试文件
    for item in result["successful"]:
        storage_path = Path(item["storage_path"])
        if storage_path.exists():
            storage_path.unlink()


@pytest.mark.asyncio
async def test_batch_upload_progress_tracking(test_video_path):
    """
    测试批量上传的进度跟踪
    
    验证需求: 10.3 - 单个文件上传完成时更新进度
    验证需求: 10.4 - 显示每个文件的上传状态和进度百分比
    """
    content = get_real_video_content(test_video_path)
    
    # 创建3个文件
    files = [
        create_upload_file(f"test_{i}.mp4", content)
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
    # 每个文件应该有：uploading -> completed
    uploading_messages = [m for m in progress_messages if m.get("status") == "uploading"]
    completed_messages = [m for m in progress_messages if m.get("status") == "completed"]
    
    assert len(uploading_messages) == 3
    assert len(completed_messages) == 3
    
    # 验证每个消息包含必要字段
    for msg in uploading_messages:
        assert "file_index" in msg
        assert "filename" in msg
        assert "progress" in msg
        assert "completed" in msg
        assert "total" in msg
        assert msg["type"] == "batch_upload_progress"
    
    for msg in completed_messages:
        assert "file_index" in msg
        assert "filename" in msg
        assert "video_id" in msg
        assert msg["progress"] == 100
        assert msg["type"] == "batch_upload_progress"
    
    # 验证最后有完成消息
    complete_messages = [m for m in progress_messages if m.get("type") == "batch_upload_complete"]
    assert len(complete_messages) == 1
    assert complete_messages[0]["total"] == 3
    assert complete_messages[0]["success_count"] == 3
    assert complete_messages[0]["failed_count"] == 0
    
    # 清理测试文件
    for item in result["successful"]:
        storage_path = Path(item["storage_path"])
        if storage_path.exists():
            storage_path.unlink()


@pytest.mark.asyncio
async def test_batch_upload_error_isolation(test_video_path):
    """
    测试批量上传的错误隔离
    
    验证需求: 10.5 - 单个文件上传失败不影响其他文件
    """
    content = get_real_video_content(test_video_path)
    
    # 创建混合文件：2个有效，1个无效格式
    files = [
        create_upload_file("test1.mp4", content),
        create_upload_file("test2.wmv", b"fake content"),  # 不支持的格式
        create_upload_file("test3.avi", content),
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
    assert result["success_count"] == 2
    assert result["failed_count"] == 1
    
    # 验证成功的文件
    assert len(result["successful"]) == 2
    successful_filenames = [item["filename"] for item in result["successful"]]
    assert "test1.mp4" in successful_filenames
    assert "test3.avi" in successful_filenames
    
    # 验证失败的文件
    assert len(result["failed"]) == 1
    assert result["failed"][0]["filename"] == "test2.wmv"
    assert "error" in result["failed"][0]
    
    # 验证进度消息中包含失败状态
    failed_messages = [m for m in progress_messages if m.get("status") == "failed"]
    assert len(failed_messages) == 1
    assert failed_messages[0]["filename"] == "test2.wmv"
    assert "error" in failed_messages[0]
    
    # 验证完成消息
    complete_messages = [m for m in progress_messages if m.get("type") == "batch_upload_complete"]
    assert len(complete_messages) == 1
    assert complete_messages[0]["success_count"] == 2
    assert complete_messages[0]["failed_count"] == 1
    
    # 清理测试文件
    for item in result["successful"]:
        storage_path = Path(item["storage_path"])
        if storage_path.exists():
            storage_path.unlink()


@pytest.mark.asyncio
async def test_batch_upload_without_websocket(test_video_path):
    """
    测试批量上传在没有WebSocket的情况下正常工作
    
    验证：WebSocket是可选的，不影响核心功能
    """
    content = get_real_video_content(test_video_path)
    
    # 创建3个文件
    files = [
        create_upload_file(f"test_{i}.mp4", content)
        for i in range(3)
    ]
    
    # 执行批量上传（不提供WebSocket回调）
    result = await upload_batch_videos(
        files=files,
        user_id="test_user",
        websocket_callback=None,
        client_id=None
    )
    
    # 验证结果
    assert result["total"] == 3
    assert result["success_count"] == 3
    assert result["failed_count"] == 0
    
    # 清理测试文件
    for item in result["successful"]:
        storage_path = Path(item["storage_path"])
        if storage_path.exists():
            storage_path.unlink()


@pytest.mark.asyncio
async def test_batch_upload_max_limit():
    """
    测试批量上传的最大文件数限制
    
    验证需求: 10.1 - 接受最多50个视频文件
    """
    from fastapi import HTTPException
    
    # 创建51个文件（超过限制）
    files = [
        create_upload_file(f"test_{i}.mp4", b"fake content")
        for i in range(51)
    ]
    
    # 执行批量上传，应该抛出异常
    with pytest.raises(HTTPException) as exc_info:
        await upload_batch_videos(
            files=files,
            user_id="test_user"
        )
    
    # 验证错误消息
    assert "50" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_batch_upload_file_index_tracking(test_video_path):
    """
    测试批量上传的文件索引跟踪
    
    验证：每个文件的进度消息包含正确的索引
    """
    content = get_real_video_content(test_video_path)
    
    # 创建5个文件
    files = [
        create_upload_file(f"test_{i}.mp4", content)
        for i in range(5)
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
    assert result["success_count"] == 5
    
    # 验证每个文件的索引
    uploading_messages = [m for m in progress_messages if m.get("status") == "uploading"]
    file_indices = [m["file_index"] for m in uploading_messages]
    
    # 应该包含0-4的所有索引
    assert set(file_indices) == {0, 1, 2, 3, 4}
    
    # 验证结果中也包含索引
    for item in result["successful"]:
        assert "index" in item
        assert 0 <= item["index"] < 5
    
    # 清理测试文件
    for item in result["successful"]:
        storage_path = Path(item["storage_path"])
        if storage_path.exists():
            storage_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
