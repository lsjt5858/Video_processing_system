"""
测试视频帧提取功能
"""

import pytest
import asyncio
from pathlib import Path
from app.watermark_detection import (
    extract_key_frames,
    generate_thumbnail,
    extract_frames_for_preview,
    FrameExtractionError
)


# 测试视频路径
TEST_VIDEO_PATH = Path(__file__).parent / "test_videos" / "test_video.mp4"
BASE_DIR = Path(__file__).parent.parent
THUMBNAIL_DIR = BASE_DIR / "thumbnails"


@pytest.mark.asyncio
async def test_extract_key_frames():
    """测试提取关键帧"""
    if not TEST_VIDEO_PATH.exists():
        pytest.skip("测试视频不存在")
    
    # 提取10帧
    frames = await extract_key_frames(str(TEST_VIDEO_PATH), num_frames=10)
    
    # 验证返回结果
    assert len(frames) > 0, "应该提取到至少一帧"
    assert len(frames) <= 10, "提取的帧数不应超过请求数量"
    
    # 验证每个帧的结构
    for frame_idx, thumbnail_path in frames:
        assert isinstance(frame_idx, int), "帧索引应该是整数"
        assert frame_idx >= 0, "帧索引应该非负"
        
        if thumbnail_path:
            assert Path(thumbnail_path).exists(), f"缩略图文件应该存在: {thumbnail_path}"
            assert thumbnail_path.endswith('.jpg'), "缩略图应该是JPG格式"
    
    print(f"✓ 成功提取 {len(frames)} 帧")


@pytest.mark.asyncio
async def test_generate_thumbnail():
    """测试生成缩略图"""
    if not TEST_VIDEO_PATH.exists():
        pytest.skip("测试视频不存在")
    
    # 生成第一帧的缩略图
    thumbnail_path = await generate_thumbnail(str(TEST_VIDEO_PATH), timestamp=0.0)
    
    # 验证缩略图文件
    assert thumbnail_path is not None, "应该返回缩略图路径"
    assert Path(thumbnail_path).exists(), "缩略图文件应该存在"
    assert thumbnail_path.endswith('.jpg'), "缩略图应该是JPG格式"
    
    print(f"✓ 成功生成缩略图: {thumbnail_path}")


@pytest.mark.asyncio
async def test_extract_frames_for_preview():
    """测试提取预览帧"""
    if not TEST_VIDEO_PATH.exists():
        pytest.skip("测试视频不存在")
    
    video_id = "test_video"
    
    # 提取预览帧
    frame_info_list = await extract_frames_for_preview(
        str(TEST_VIDEO_PATH),
        video_id,
        num_frames=5
    )
    
    # 验证返回结果
    assert len(frame_info_list) > 0, "应该返回至少一个帧信息"
    assert len(frame_info_list) <= 5, "返回的帧数不应超过请求数量"
    
    # 验证每个帧信息的结构
    for frame_info in frame_info_list:
        assert "frame_index" in frame_info, "应该包含frame_index字段"
        assert "timestamp" in frame_info, "应该包含timestamp字段"
        assert "thumbnail_url" in frame_info, "应该包含thumbnail_url字段"
        
        assert isinstance(frame_info["frame_index"], int), "frame_index应该是整数"
        assert frame_info["frame_index"] >= 0, "frame_index应该非负"
        
        assert isinstance(frame_info["timestamp"], (int, float)), "timestamp应该是数字"
        assert frame_info["timestamp"] >= 0, "timestamp应该非负"
        
        assert frame_info["thumbnail_url"].startswith("/thumbnails/"), "thumbnail_url应该是正确的URL格式"
    
    print(f"✓ 成功提取 {len(frame_info_list)} 个预览帧")
    for frame_info in frame_info_list:
        print(f"  - 帧 {frame_info['frame_index']}: {frame_info['timestamp']}s -> {frame_info['thumbnail_url']}")


@pytest.mark.asyncio
async def test_extract_frames_invalid_video():
    """测试无效视频文件"""
    invalid_path = "/path/to/nonexistent/video.mp4"
    
    with pytest.raises(FrameExtractionError):
        await extract_key_frames(invalid_path)
    
    print("✓ 正确处理无效视频文件")


@pytest.mark.asyncio
async def test_thumbnail_directory_creation():
    """测试缩略图目录创建"""
    # 确保缩略图目录存在
    assert THUMBNAIL_DIR.exists(), "缩略图目录应该存在"
    assert THUMBNAIL_DIR.is_dir(), "缩略图路径应该是目录"
    
    print(f"✓ 缩略图目录存在: {THUMBNAIL_DIR}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_extract_key_frames())
    asyncio.run(test_generate_thumbnail())
    asyncio.run(test_extract_frames_for_preview())
    asyncio.run(test_extract_frames_invalid_video())
    asyncio.run(test_thumbnail_directory_creation())
    
    print("\n所有测试通过！")
