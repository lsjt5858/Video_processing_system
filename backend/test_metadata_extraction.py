"""
测试视频元数据提取功能
"""
import sys
from pathlib import Path

# 添加app目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.video_import import extract_video_metadata, MetadataExtractionError


def test_extract_metadata():
    """测试元数据提取"""
    test_video = Path(__file__).parent / "test_videos" / "test_video.mp4"
    
    if not test_video.exists():
        print(f"错误: 测试视频不存在: {test_video}")
        return False
    
    try:
        print(f"提取视频元数据: {test_video}")
        metadata = extract_video_metadata(str(test_video))
        
        print("\n提取的元数据:")
        print(f"  分辨率: {metadata['resolution']}")
        print(f"  时长: {metadata['duration']:.2f} 秒")
        print(f"  编码: {metadata['codec']}")
        print(f"  帧率: {metadata['framerate']:.2f} fps")
        print(f"  码率: {metadata['bitrate']} bps")
        print(f"  文件大小: {metadata['file_size']} 字节")
        
        # 验证必需字段
        assert metadata['resolution'][0] > 0, "分辨率宽度必须大于0"
        assert metadata['resolution'][1] > 0, "分辨率高度必须大于0"
        assert metadata['duration'] > 0, "时长必须大于0"
        assert metadata['framerate'] > 0, "帧率必须大于0"
        assert metadata['file_size'] > 0, "文件大小必须大于0"
        assert metadata['codec'] != 'unknown', "编码格式不应为unknown"
        
        print("\n✓ 元数据提取成功！所有字段验证通过。")
        return True
        
    except MetadataExtractionError as e:
        print(f"\n✗ 元数据提取失败: {e}")
        return False
    except AssertionError as e:
        print(f"\n✗ 验证失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_extract_metadata()
    sys.exit(0 if success else 1)
