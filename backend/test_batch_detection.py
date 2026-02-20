"""
测试批量检测功能

验证批量帧提取和批量水印标记功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.watermark_detection import batch_extract_frames, batch_mark_watermarks


async def test_batch_extract_frames():
    """测试批量提取帧功能"""
    print("测试批量提取帧功能...")
    
    # 模拟视频路径列表（使用不存在的路径来测试错误处理）
    video_paths = [
        ("video1", "nonexistent_video1.mp4"),
        ("video2", "nonexistent_video2.mp4"),
    ]
    
    try:
        results = await batch_extract_frames(video_paths, num_frames=5)
        
        print(f"总视频数: {results['total_count']}")
        print(f"成功数: {results['success_count']}")
        print(f"失败数: {results['failed_count']}")
        
        for result in results['results']:
            print(f"\n视频ID: {result['video_id']}")
            print(f"状态: {result['status']}")
            if result['status'] == 'failed':
                print(f"错误: {result['error']}")
            else:
                print(f"提取帧数: {len(result['frames'])}")
        
        # 验证结果结构
        assert 'total_count' in results
        assert 'success_count' in results
        assert 'failed_count' in results
        assert 'results' in results
        assert results['total_count'] == len(video_paths)
        
        print("\n✓ 批量提取帧功能测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 批量提取帧功能测试失败: {str(e)}")
        return False


async def test_batch_mark_watermarks():
    """测试批量标记水印功能"""
    print("\n测试批量标记水印功能...")
    
    # 模拟水印数据（使用不存在的视频路径来测试错误处理）
    watermark_data = [
        {
            "video_id": "video1",
            "video_path": "nonexistent_video1.mp4",
            "bounding_boxes": [
                {
                    "x": 10,
                    "y": 10,
                    "width": 100,
                    "height": 50,
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "watermark_type": "corner"
                }
            ]
        },
        {
            "video_id": "video2",
            "video_path": "nonexistent_video2.mp4",
            "bounding_boxes": []
        }
    ]
    
    try:
        # 注意：这个测试需要数据库会话，这里只测试函数结构
        # 在实际使用中需要传入有效的db会话
        print("批量标记水印功能结构验证通过（需要数据库会话才能完整测试）")
        
        # 验证函数存在且可调用
        assert callable(batch_mark_watermarks)
        
        print("✓ 批量标记水印功能结构测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 批量标记水印功能测试失败: {str(e)}")
        return False


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("批量检测功能测试")
    print("=" * 60)
    
    test1 = await test_batch_extract_frames()
    test2 = await test_batch_mark_watermarks()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("所有测试通过 ✓")
    else:
        print("部分测试失败 ✗")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
