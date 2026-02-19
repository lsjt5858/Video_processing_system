"""
测试数据库功能
"""
import asyncio
import uuid
from datetime import datetime
from sqlalchemy import select
from app.database import init_db, close_db, AsyncSessionLocal, Video, WatermarkRegion, ProcessingTask


async def test_database():
    """测试数据库基本功能"""
    print("开始测试数据库...")
    
    # 初始化数据库
    await init_db()
    
    # 创建会话
    async with AsyncSessionLocal() as session:
        # 测试1: 创建视频记录
        print("\n测试1: 创建视频记录")
        video_id = f"vid_{uuid.uuid4().hex[:8]}"
        video = Video(
            video_id=video_id,
            user_id="test_user_001",
            format="mp4",
            resolution_width=1920,
            resolution_height=1080,
            duration=120.5,
            codec="h264",
            framerate=30.0,
            bitrate=5000000,
            file_size=104857600,
            storage_path="/uploads/test_video.mp4",
            import_source="local",
            created_at=datetime.now()
        )
        session.add(video)
        await session.commit()
        print(f"✓ 视频记录创建成功: {video}")
        
        # 测试2: 创建水印区域记录
        print("\n测试2: 创建水印区域记录")
        region_id = f"reg_{uuid.uuid4().hex[:8]}"
        watermark = WatermarkRegion(
            region_id=region_id,
            video_id=video_id,
            bbox_x=100,
            bbox_y=50,
            bbox_width=200,
            bbox_height=100,
            start_time=0.0,
            end_time=120.5,
            confidence=0.95,
            watermark_type="corner",
            detection_method="auto",
            created_at=datetime.now()
        )
        session.add(watermark)
        await session.commit()
        print(f"✓ 水印区域记录创建成功: {watermark}")
        
        # 测试3: 创建处理任务记录
        print("\n测试3: 创建处理任务记录")
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = ProcessingTask(
            task_id=task_id,
            user_id="test_user_001",
            video_id=video_id,
            task_type="removal",
            status="pending",
            parameters={"mode": "crop_reconstruct", "regions": [region_id]},
            created_at=datetime.now()
        )
        session.add(task)
        await session.commit()
        print(f"✓ 处理任务记录创建成功: {task}")
        
        # 测试4: 查询视频记录
        print("\n测试4: 查询视频记录")
        result = await session.execute(
            select(Video).where(Video.video_id == video_id)
        )
        found_video = result.scalar_one_or_none()
        if found_video:
            print(f"✓ 查询成功: {found_video}")
        else:
            print("✗ 查询失败")
        
        # 测试5: 查询关联的水印区域
        print("\n测试5: 查询关联的水印区域")
        result = await session.execute(
            select(WatermarkRegion).where(WatermarkRegion.video_id == video_id)
        )
        watermarks = result.scalars().all()
        print(f"✓ 找到 {len(watermarks)} 个水印区域")
        for wm in watermarks:
            print(f"  - {wm}")
        
        # 测试6: 查询关联的处理任务
        print("\n测试6: 查询关联的处理任务")
        result = await session.execute(
            select(ProcessingTask).where(ProcessingTask.video_id == video_id)
        )
        tasks = result.scalars().all()
        print(f"✓ 找到 {len(tasks)} 个处理任务")
        for t in tasks:
            print(f"  - {t}")
        
        # 测试7: 更新任务状态
        print("\n测试7: 更新任务状态")
        task.status = "completed"
        task.completed_at = datetime.now()
        task.result = {"output_path": "/outputs/processed_video.mp4"}
        await session.commit()
        print(f"✓ 任务状态更新成功: {task.status}")
        
        # 测试8: 测试级联删除
        print("\n测试8: 测试级联删除")
        await session.delete(found_video)
        await session.commit()
        print("✓ 视频记录删除成功")
        
        # 验证级联删除
        result = await session.execute(
            select(WatermarkRegion).where(WatermarkRegion.video_id == video_id)
        )
        remaining_watermarks = result.scalars().all()
        result = await session.execute(
            select(ProcessingTask).where(ProcessingTask.video_id == video_id)
        )
        remaining_tasks = result.scalars().all()
        
        if len(remaining_watermarks) == 0 and len(remaining_tasks) == 0:
            print("✓ 级联删除成功，关联记录已清除")
        else:
            print(f"✗ 级联删除失败，仍有 {len(remaining_watermarks)} 个水印区域和 {len(remaining_tasks)} 个任务")
    
    # 关闭数据库
    await close_db()
    
    print("\n所有测试完成！")


if __name__ == "__main__":
    asyncio.run(test_database())
