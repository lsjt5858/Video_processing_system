"""
数据访问层 (CRUD Operations)

实现视频、水印区域和处理任务的异步CRUD操作
使用SQLAlchemy AsyncSession进行数据库操作
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import Video, WatermarkRegion, ProcessingTask


# ==================== 视频 CRUD 操作 ====================

async def create_video(
    db: AsyncSession,
    video_id: str,
    user_id: str,
    format: str,
    resolution_width: int,
    resolution_height: int,
    duration: float,
    codec: str,
    framerate: float,
    bitrate: int,
    file_size: int,
    storage_path: str,
    import_source: str
) -> Video:
    """
    创建新视频记录
    
    参数:
        db: 数据库会话
        video_id: 视频唯一标识
        user_id: 用户ID
        format: 视频格式 (mp4, avi, mov, mkv)
        resolution_width: 分辨率宽度
        resolution_height: 分辨率高度
        duration: 视频时长（秒）
        codec: 编码格式
        framerate: 帧率
        bitrate: 码率
        file_size: 文件大小（字节）
        storage_path: 存储路径
        import_source: 导入来源 (local, platform, url)
    
    返回:
        Video: 创建的视频对象
    """
    video = Video(
        video_id=video_id,
        user_id=user_id,
        format=format,
        resolution_width=resolution_width,
        resolution_height=resolution_height,
        duration=duration,
        codec=codec,
        framerate=framerate,
        bitrate=bitrate,
        file_size=file_size,
        storage_path=storage_path,
        import_source=import_source,
        created_at=datetime.now()
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)
    return video


async def get_video_by_id(db: AsyncSession, video_id: str) -> Optional[Video]:
    """
    根据ID获取视频
    
    参数:
        db: 数据库会话
        video_id: 视频ID
    
    返回:
        Optional[Video]: 视频对象，不存在则返回None
    """
    result = await db.execute(
        select(Video).where(Video.video_id == video_id)
    )
    return result.scalar_one_or_none()


async def get_video_with_relations(db: AsyncSession, video_id: str) -> Optional[Video]:
    """
    获取视频及其关联的水印区域和处理任务
    
    参数:
        db: 数据库会话
        video_id: 视频ID
    
    返回:
        Optional[Video]: 包含关联数据的视频对象
    """
    result = await db.execute(
        select(Video)
        .options(
            selectinload(Video.watermark_regions),
            selectinload(Video.processing_tasks)
        )
        .where(Video.video_id == video_id)
    )
    return result.scalar_one_or_none()


async def get_videos_by_user(
    db: AsyncSession,
    user_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[Video]:
    """
    获取用户的视频列表（分页）
    
    参数:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    返回:
        List[Video]: 视频列表
    """
    result = await db.execute(
        select(Video)
        .where(Video.user_id == user_id)
        .order_by(Video.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_videos_count_by_user(db: AsyncSession, user_id: str) -> int:
    """
    获取用户的视频总数
    
    参数:
        db: 数据库会话
        user_id: 用户ID
    
    返回:
        int: 视频总数
    """
    result = await db.execute(
        select(func.count(Video.video_id)).where(Video.user_id == user_id)
    )
    return result.scalar_one()


async def get_all_videos_count(db: AsyncSession) -> int:
    """
    获取所有视频的总数
    
    参数:
        db: 数据库会话
    
    返回:
        int: 视频总数
    """
    result = await db.execute(
        select(func.count(Video.video_id))
    )
    return result.scalar_one()


async def get_all_videos(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Video]:
    """
    获取所有视频列表（分页）
    
    参数:
        db: 数据库会话
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    返回:
        List[Video]: 视频列表
    """
    result = await db.execute(
        select(Video)
        .order_by(Video.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_video(
    db: AsyncSession,
    video_id: str,
    **kwargs
) -> Optional[Video]:
    """
    更新视频信息
    
    参数:
        db: 数据库会话
        video_id: 视频ID
        **kwargs: 要更新的字段
    
    返回:
        Optional[Video]: 更新后的视频对象
    """
    await db.execute(
        update(Video)
        .where(Video.video_id == video_id)
        .values(**kwargs)
    )
    await db.flush()
    return await get_video_by_id(db, video_id)


async def delete_video(db: AsyncSession, video_id: str) -> bool:
    """
    删除视频（级联删除关联的水印区域和任务）
    
    参数:
        db: 数据库会话
        video_id: 视频ID
    
    返回:
        bool: 是否成功删除
    """
    result = await db.execute(
        delete(Video).where(Video.video_id == video_id)
    )
    await db.flush()
    return result.rowcount > 0


# ==================== 水印区域 CRUD 操作 ====================

async def create_watermark_region(
    db: AsyncSession,
    region_id: str,
    video_id: str,
    bbox_x: int,
    bbox_y: int,
    bbox_width: int,
    bbox_height: int,
    start_time: float,
    end_time: float,
    confidence: float,
    watermark_type: str,
    detection_method: str
) -> WatermarkRegion:
    """
    创建水印区域记录
    
    参数:
        db: 数据库会话
        region_id: 区域唯一标识
        video_id: 视频ID
        bbox_x: 边界框左上角x坐标
        bbox_y: 边界框左上角y坐标
        bbox_width: 边界框宽度
        bbox_height: 边界框高度
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        confidence: 置信度 (0-1)
        watermark_type: 水印类型 (corner, rolling, logo, subtitle)
        detection_method: 检测方法 (auto, manual)
    
    返回:
        WatermarkRegion: 创建的水印区域对象
    """
    region = WatermarkRegion(
        region_id=region_id,
        video_id=video_id,
        bbox_x=bbox_x,
        bbox_y=bbox_y,
        bbox_width=bbox_width,
        bbox_height=bbox_height,
        start_time=start_time,
        end_time=end_time,
        confidence=confidence,
        watermark_type=watermark_type,
        detection_method=detection_method,
        created_at=datetime.now()
    )
    db.add(region)
    await db.flush()
    await db.refresh(region)
    return region


async def get_watermark_region_by_id(
    db: AsyncSession,
    region_id: str
) -> Optional[WatermarkRegion]:
    """
    根据ID获取水印区域
    
    参数:
        db: 数据库会话
        region_id: 区域ID
    
    返回:
        Optional[WatermarkRegion]: 水印区域对象，不存在则返回None
    """
    result = await db.execute(
        select(WatermarkRegion).where(WatermarkRegion.region_id == region_id)
    )
    return result.scalar_one_or_none()


async def get_watermark_regions_by_video(
    db: AsyncSession,
    video_id: str
) -> List[WatermarkRegion]:
    """
    获取视频的所有水印区域
    
    参数:
        db: 数据库会话
        video_id: 视频ID
    
    返回:
        List[WatermarkRegion]: 水印区域列表
    """
    result = await db.execute(
        select(WatermarkRegion)
        .where(WatermarkRegion.video_id == video_id)
        .order_by(WatermarkRegion.created_at)
    )
    return list(result.scalars().all())


async def get_watermark_regions_by_type(
    db: AsyncSession,
    video_id: str,
    watermark_type: str
) -> List[WatermarkRegion]:
    """
    获取视频中特定类型的水印区域
    
    参数:
        db: 数据库会话
        video_id: 视频ID
        watermark_type: 水印类型
    
    返回:
        List[WatermarkRegion]: 水印区域列表
    """
    result = await db.execute(
        select(WatermarkRegion)
        .where(
            WatermarkRegion.video_id == video_id,
            WatermarkRegion.watermark_type == watermark_type
        )
        .order_by(WatermarkRegion.created_at)
    )
    return list(result.scalars().all())


async def update_watermark_region(
    db: AsyncSession,
    region_id: str,
    **kwargs
) -> Optional[WatermarkRegion]:
    """
    更新水印区域信息
    
    参数:
        db: 数据库会话
        region_id: 区域ID
        **kwargs: 要更新的字段
    
    返回:
        Optional[WatermarkRegion]: 更新后的水印区域对象
    """
    await db.execute(
        update(WatermarkRegion)
        .where(WatermarkRegion.region_id == region_id)
        .values(**kwargs)
    )
    await db.flush()
    return await get_watermark_region_by_id(db, region_id)


async def delete_watermark_region(db: AsyncSession, region_id: str) -> bool:
    """
    删除水印区域
    
    参数:
        db: 数据库会话
        region_id: 区域ID
    
    返回:
        bool: 是否成功删除
    """
    result = await db.execute(
        delete(WatermarkRegion).where(WatermarkRegion.region_id == region_id)
    )
    await db.flush()
    return result.rowcount > 0


async def delete_watermark_regions_by_video(db: AsyncSession, video_id: str) -> int:
    """
    删除视频的所有水印区域
    
    参数:
        db: 数据库会话
        video_id: 视频ID
    
    返回:
        int: 删除的记录数
    """
    result = await db.execute(
        delete(WatermarkRegion).where(WatermarkRegion.video_id == video_id)
    )
    await db.flush()
    return result.rowcount


# ==================== 处理任务 CRUD 操作 ====================

async def create_processing_task(
    db: AsyncSession,
    task_id: str,
    user_id: str,
    video_id: str,
    task_type: str,
    status: str,
    parameters: dict
) -> ProcessingTask:
    """
    创建处理任务记录
    
    参数:
        db: 数据库会话
        task_id: 任务唯一标识
        user_id: 用户ID
        video_id: 视频ID
        task_type: 任务类型 (detection, removal, optimization)
        status: 任务状态 (pending, processing, completed, failed)
        parameters: 任务参数（JSON）
    
    返回:
        ProcessingTask: 创建的任务对象
    """
    task = ProcessingTask(
        task_id=task_id,
        user_id=user_id,
        video_id=video_id,
        task_type=task_type,
        status=status,
        parameters=parameters,
        created_at=datetime.now()
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_task_by_id(db: AsyncSession, task_id: str) -> Optional[ProcessingTask]:
    """
    根据ID获取任务
    
    参数:
        db: 数据库会话
        task_id: 任务ID
    
    返回:
        Optional[ProcessingTask]: 任务对象，不存在则返回None
    """
    result = await db.execute(
        select(ProcessingTask).where(ProcessingTask.task_id == task_id)
    )
    return result.scalar_one_or_none()


async def get_tasks_by_user(
    db: AsyncSession,
    user_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[ProcessingTask]:
    """
    获取用户的任务列表（分页）
    
    参数:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    返回:
        List[ProcessingTask]: 任务列表
    """
    result = await db.execute(
        select(ProcessingTask)
        .where(ProcessingTask.user_id == user_id)
        .order_by(ProcessingTask.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_tasks_by_video(
    db: AsyncSession,
    video_id: str
) -> List[ProcessingTask]:
    """
    获取视频的所有任务
    
    参数:
        db: 数据库会话
        video_id: 视频ID
    
    返回:
        List[ProcessingTask]: 任务列表
    """
    result = await db.execute(
        select(ProcessingTask)
        .where(ProcessingTask.video_id == video_id)
        .order_by(ProcessingTask.created_at.desc())
    )
    return list(result.scalars().all())


async def get_tasks_by_status(
    db: AsyncSession,
    status: str,
    skip: int = 0,
    limit: int = 100
) -> List[ProcessingTask]:
    """
    根据状态获取任务列表
    
    参数:
        db: 数据库会话
        status: 任务状态
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    返回:
        List[ProcessingTask]: 任务列表
    """
    result = await db.execute(
        select(ProcessingTask)
        .where(ProcessingTask.status == status)
        .order_by(ProcessingTask.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_tasks_by_user_and_status(
    db: AsyncSession,
    user_id: str,
    status: str,
    skip: int = 0,
    limit: int = 100
) -> List[ProcessingTask]:
    """
    获取用户特定状态的任务列表
    
    参数:
        db: 数据库会话
        user_id: 用户ID
        status: 任务状态
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    返回:
        List[ProcessingTask]: 任务列表
    """
    result = await db.execute(
        select(ProcessingTask)
        .where(
            ProcessingTask.user_id == user_id,
            ProcessingTask.status == status
        )
        .order_by(ProcessingTask.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_task_status(
    db: AsyncSession,
    task_id: str,
    status: str,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    error_message: Optional[str] = None,
    result: Optional[dict] = None
) -> Optional[ProcessingTask]:
    """
    更新任务状态
    
    参数:
        db: 数据库会话
        task_id: 任务ID
        status: 新状态
        started_at: 开始时间（可选）
        completed_at: 完成时间（可选）
        error_message: 错误信息（可选）
        result: 任务结果（可选）
    
    返回:
        Optional[ProcessingTask]: 更新后的任务对象
    """
    update_data = {"status": status}
    if started_at is not None:
        update_data["started_at"] = started_at
    if completed_at is not None:
        update_data["completed_at"] = completed_at
    if error_message is not None:
        update_data["error_message"] = error_message
    if result is not None:
        update_data["result"] = result
    
    await db.execute(
        update(ProcessingTask)
        .where(ProcessingTask.task_id == task_id)
        .values(**update_data)
    )
    await db.flush()
    return await get_task_by_id(db, task_id)


async def update_task(
    db: AsyncSession,
    task_id: str,
    **kwargs
) -> Optional[ProcessingTask]:
    """
    更新任务信息
    
    参数:
        db: 数据库会话
        task_id: 任务ID
        **kwargs: 要更新的字段
    
    返回:
        Optional[ProcessingTask]: 更新后的任务对象
    """
    await db.execute(
        update(ProcessingTask)
        .where(ProcessingTask.task_id == task_id)
        .values(**kwargs)
    )
    await db.flush()
    return await get_task_by_id(db, task_id)


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    """
    删除任务
    
    参数:
        db: 数据库会话
        task_id: 任务ID
    
    返回:
        bool: 是否成功删除
    """
    result = await db.execute(
        delete(ProcessingTask).where(ProcessingTask.task_id == task_id)
    )
    await db.flush()
    return result.rowcount > 0


async def delete_tasks_by_video(db: AsyncSession, video_id: str) -> int:
    """
    删除视频的所有任务
    
    参数:
        db: 数据库会话
        video_id: 视频ID
    
    返回:
        int: 删除的记录数
    """
    result = await db.execute(
        delete(ProcessingTask).where(ProcessingTask.video_id == video_id)
    )
    await db.flush()
    return result.rowcount
