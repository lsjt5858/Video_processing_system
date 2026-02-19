"""
数据库配置和ORM模型

使用SQLAlchemy定义ORM模型，使用aiosqlite实现异步数据库操作
"""

from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey,
    Index, create_engine
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./video_platform.db")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 开发环境打印SQL语句
    future=True,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基类
Base = declarative_base()


# ORM模型定义

class Video(Base):
    """视频表"""
    __tablename__ = "videos"

    video_id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    format = Column(String(10), nullable=False)
    resolution_width = Column(Integer, nullable=False)
    resolution_height = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)
    codec = Column(String(20), nullable=False)
    framerate = Column(Float, nullable=False)
    bitrate = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    import_source = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # 关系
    watermark_regions = relationship(
        "WatermarkRegion",
        back_populates="video",
        cascade="all, delete-orphan"
    )
    processing_tasks = relationship(
        "ProcessingTask",
        back_populates="video",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Video(video_id={self.video_id}, format={self.format}, resolution={self.resolution_width}x{self.resolution_height})>"


class WatermarkRegion(Base):
    """水印区域表"""
    __tablename__ = "watermark_regions"

    region_id = Column(String(36), primary_key=True, index=True)
    video_id = Column(String(36), ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False, index=True)
    bbox_x = Column(Integer, nullable=False)
    bbox_y = Column(Integer, nullable=False)
    bbox_width = Column(Integer, nullable=False)
    bbox_height = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    watermark_type = Column(String(20), nullable=False)
    detection_method = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 关系
    video = relationship("Video", back_populates="watermark_regions")

    def __repr__(self):
        return f"<WatermarkRegion(region_id={self.region_id}, video_id={self.video_id}, type={self.watermark_type})>"


class ProcessingTask(Base):
    """处理任务表"""
    __tablename__ = "processing_tasks"

    task_id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    video_id = Column(String(36), ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    parameters = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    result = Column(JSON, nullable=True)

    # 关系
    video = relationship("Video", back_populates="processing_tasks")

    def __repr__(self):
        return f"<ProcessingTask(task_id={self.task_id}, type={self.task_type}, status={self.status})>"


# 数据库初始化和连接管理

async def init_db():
    """
    初始化数据库，创建所有表
    
    在应用启动时调用此函数
    """
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    print("数据库初始化完成")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    用于依赖注入，在FastAPI路由中使用
    
    示例:
        @app.get("/videos")
        async def get_videos(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Video))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """
    关闭数据库连接
    
    在应用关闭时调用此函数
    """
    await engine.dispose()
    print("数据库连接已关闭")


# 索引定义（已在Column定义中通过index=True实现）
# 额外的复合索引可以在这里定义

# 为videos表创建复合索引
Index('idx_videos_user_created', Video.user_id, Video.created_at)

# 为processing_tasks表创建复合索引
Index('idx_tasks_user_status', ProcessingTask.user_id, ProcessingTask.status)
Index('idx_tasks_video_status', ProcessingTask.video_id, ProcessingTask.status)
