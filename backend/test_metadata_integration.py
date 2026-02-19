"""
集成测试：测试视频上传和元数据提取
"""
import pytest
import asyncio
import io
from pathlib import Path

# 添加app目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.video_import import (
    upload_single_video,
    extract_video_metadata,
    MetadataExtractionError
)
from fastapi import UploadFile


@pytest.mark.asyncio
async def test_upload_with_real_video():
    """测试使用真实视频文件上传和元数据提取"""
    test_video_path = Path(__file__).parent / "test_videos" / "test_video.mp4"
    
    if not test_video_path.exists():
        pytest.skip("测试视频不存在")
    
    # 读取测试视频文件
    with open(test_video_path, "rb") as f:
        content = f.read()
    
    # 创建UploadFile对象
    file_obj = io.BytesIO(content)
    upload_file = UploadFile(filename="test_upload.mp4", file=file_obj)
    
    try:
        # 上传视频
        result = await upload_single_video(upload_file, user_id="test_user")
        
        # 验证返回结果
        assert result.video_id is not None
        assert result.metadata.format.value == "mp4"
        assert result.metadata.file_size == len(content)
        assert result.import_source == "local"
        
        # 验证元数据字段
        metadata = result.metadata
        print(f"\n提取的元数据:")
        print(f"  分辨率: {metadata.resolution}")
        print(f"  时长: {metadata.duration:.2f} 秒")
        print(f"  编码: {metadata.codec}")
        print(f"  帧率: {metadata.framerate:.2f} fps")
        print(f"  码率: {metadata.bitrate} bps")
        print(f"  文件大小: {metadata.file_size} 字节")
        
        # 验证元数据完整性（属性2：视频元数据完整性）
        assert metadata.resolution[0] > 0, "分辨率宽度必须大于0"
        assert metadata.resolution[1] > 0, "分辨率高度必须大于0"
        assert metadata.duration > 0, "时长必须大于0"
        assert metadata.codec != "unknown", "编码格式不应为unknown"
        assert metadata.framerate > 0, "帧率必须大于0"
        assert metadata.bitrate >= 0, "码率必须大于等于0"
        
        # 验证存储路径
        assert Path(result.storage_path).exists()
        
        # 清理测试文件
        Path(result.storage_path).unlink()
        
        print("\n✓ 视频上传和元数据提取测试通过！")
        
    except Exception as e:
        pytest.fail(f"测试失败: {str(e)}")


def test_extract_metadata_from_real_video():
    """测试从真实视频提取元数据"""
    test_video_path = Path(__file__).parent / "test_videos" / "test_video.mp4"
    
    if not test_video_path.exists():
        pytest.skip("测试视频不存在")
    
    # 提取元数据
    metadata = extract_video_metadata(str(test_video_path))
    
    # 验证所有必需字段都存在
    assert 'resolution' in metadata
    assert 'duration' in metadata
    assert 'codec' in metadata
    assert 'framerate' in metadata
    assert 'bitrate' in metadata
    assert 'file_size' in metadata
    
    # 验证字段值有效
    assert metadata['resolution'][0] == 1280
    assert metadata['resolution'][1] == 720
    assert metadata['duration'] > 0
    assert metadata['codec'] == 'h264'
    assert metadata['framerate'] == 30.0
    assert metadata['bitrate'] > 0
    assert metadata['file_size'] > 0
    
    print(f"\n✓ 元数据提取测试通过！")
    print(f"  分辨率: {metadata['resolution']}")
    print(f"  时长: {metadata['duration']:.2f} 秒")
    print(f"  编码: {metadata['codec']}")
    print(f"  帧率: {metadata['framerate']:.2f} fps")


def test_extract_metadata_invalid_file():
    """测试从无效文件提取元数据应该失败"""
    # 创建一个临时的无效文件
    invalid_file = Path(__file__).parent / "test_videos" / "invalid.mp4"
    invalid_file.parent.mkdir(exist_ok=True)
    
    with open(invalid_file, "wb") as f:
        f.write(b"This is not a valid video file")
    
    try:
        # 应该抛出MetadataExtractionError
        with pytest.raises(MetadataExtractionError):
            extract_video_metadata(str(invalid_file))
        
        print("\n✓ 无效文件测试通过！")
    finally:
        # 清理
        if invalid_file.exists():
            invalid_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
