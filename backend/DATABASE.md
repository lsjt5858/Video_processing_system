# 数据库实现文档

## 概述

本项目使用 SQLite 作为轻量级数据库，通过 SQLAlchemy ORM 进行数据访问，使用 aiosqlite 实现异步操作。

## 技术栈

- **数据库**: SQLite 3
- **ORM**: SQLAlchemy 2.0.23
- **异步驱动**: aiosqlite 0.19.0
- **异步支持**: greenlet 3.0.1

## 数据库架构

### 表结构

#### 1. videos（视频表）

存储视频的基本信息和元数据。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| video_id | VARCHAR(36) | 视频唯一标识 | PRIMARY KEY, INDEX |
| user_id | VARCHAR(36) | 用户ID | NOT NULL, INDEX |
| format | VARCHAR(10) | 视频格式（mp4/avi/mov/mkv） | NOT NULL |
| resolution_width | INTEGER | 分辨率宽度 | NOT NULL |
| resolution_height | INTEGER | 分辨率高度 | NOT NULL |
| duration | FLOAT | 视频时长（秒） | NOT NULL |
| codec | VARCHAR(20) | 编码格式（h264/h265等） | NOT NULL |
| framerate | FLOAT | 帧率 | NOT NULL |
| bitrate | INTEGER | 码率（bps） | NOT NULL |
| file_size | INTEGER | 文件大小（字节） | NOT NULL |
| storage_path | VARCHAR(500) | 存储路径 | NOT NULL |
| import_source | VARCHAR(20) | 导入来源（local/platform/url） | NOT NULL |
| created_at | DATETIME | 创建时间 | NOT NULL, INDEX |

**索引**:
- `ix_videos_video_id`: 主键索引
- `ix_videos_user_id`: 用户ID索引
- `ix_videos_created_at`: 创建时间索引
- `idx_videos_user_created`: 复合索引（user_id, created_at）

#### 2. watermark_regions（水印区域表）

存储检测到的水印区域信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| region_id | VARCHAR(36) | 区域唯一标识 | PRIMARY KEY, INDEX |
| video_id | VARCHAR(36) | 所属视频ID | FOREIGN KEY, NOT NULL, INDEX |
| bbox_x | INTEGER | 边界框左上角X坐标 | NOT NULL |
| bbox_y | INTEGER | 边界框左上角Y坐标 | NOT NULL |
| bbox_width | INTEGER | 边界框宽度 | NOT NULL |
| bbox_height | INTEGER | 边界框高度 | NOT NULL |
| start_time | FLOAT | 开始时间（秒） | NOT NULL |
| end_time | FLOAT | 结束时间（秒） | NOT NULL |
| confidence | FLOAT | 置信度（0-1） | NOT NULL |
| watermark_type | VARCHAR(20) | 水印类型（corner/rolling/logo/subtitle） | NOT NULL |
| detection_method | VARCHAR(10) | 检测方法（auto/manual） | NOT NULL |
| created_at | DATETIME | 创建时间 | NOT NULL |

**外键约束**:
- `video_id` → `videos.video_id` (ON DELETE CASCADE)

**索引**:
- `ix_watermark_regions_region_id`: 主键索引
- `ix_watermark_regions_video_id`: 视频ID索引

#### 3. processing_tasks（处理任务表）

存储视频处理任务的状态和结果。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| task_id | VARCHAR(36) | 任务唯一标识 | PRIMARY KEY, INDEX |
| user_id | VARCHAR(36) | 用户ID | NOT NULL, INDEX |
| video_id | VARCHAR(36) | 视频ID | FOREIGN KEY, NOT NULL |
| task_type | VARCHAR(20) | 任务类型（detection/removal/optimization） | NOT NULL |
| status | VARCHAR(20) | 任务状态（pending/processing/completed/failed） | NOT NULL, INDEX |
| parameters | JSON | 任务参数 | NOT NULL |
| created_at | DATETIME | 创建时间 | NOT NULL, INDEX |
| started_at | DATETIME | 开始时间 | NULLABLE |
| completed_at | DATETIME | 完成时间 | NULLABLE |
| error_message | VARCHAR | 错误信息 | NULLABLE |
| result | JSON | 处理结果 | NULLABLE |

**外键约束**:
- `video_id` → `videos.video_id` (ON DELETE CASCADE)

**索引**:
- `ix_processing_tasks_task_id`: 主键索引
- `ix_processing_tasks_user_id`: 用户ID索引
- `ix_processing_tasks_status`: 状态索引
- `ix_processing_tasks_created_at`: 创建时间索引
- `idx_tasks_user_status`: 复合索引（user_id, status）
- `idx_tasks_video_status`: 复合索引（video_id, status）

## 使用方法

### 1. 数据库初始化

在应用启动时自动初始化：

```python
from app.database import init_db

# 在应用启动时调用
await init_db()
```

### 2. 获取数据库会话

在 FastAPI 路由中使用依赖注入：

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

@app.get("/videos")
async def get_videos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video))
    videos = result.scalars().all()
    return videos
```

### 3. 基本 CRUD 操作

#### 创建记录

```python
from app.database import Video, AsyncSessionLocal

async with AsyncSessionLocal() as session:
    video = Video(
        video_id="vid_123",
        user_id="user_001",
        format="mp4",
        resolution_width=1920,
        resolution_height=1080,
        duration=120.5,
        codec="h264",
        framerate=30.0,
        bitrate=5000000,
        file_size=104857600,
        storage_path="/uploads/video.mp4",
        import_source="local"
    )
    session.add(video)
    await session.commit()
```

#### 查询记录

```python
from sqlalchemy import select

async with AsyncSessionLocal() as session:
    # 查询单条记录
    result = await session.execute(
        select(Video).where(Video.video_id == "vid_123")
    )
    video = result.scalar_one_or_none()
    
    # 查询多条记录
    result = await session.execute(
        select(Video).where(Video.user_id == "user_001")
    )
    videos = result.scalars().all()
```

#### 更新记录

```python
async with AsyncSessionLocal() as session:
    result = await session.execute(
        select(Video).where(Video.video_id == "vid_123")
    )
    video = result.scalar_one()
    
    video.duration = 125.0
    await session.commit()
```

#### 删除记录

```python
async with AsyncSessionLocal() as session:
    result = await session.execute(
        select(Video).where(Video.video_id == "vid_123")
    )
    video = result.scalar_one()
    
    await session.delete(video)
    await session.commit()
```

### 4. 关系查询

由于配置了 ORM 关系，可以方便地访问关联数据：

```python
# 查询视频及其所有水印区域
async with AsyncSessionLocal() as session:
    result = await session.execute(
        select(Video).where(Video.video_id == "vid_123")
    )
    video = result.scalar_one()
    
    # 访问关联的水印区域（需要显式加载）
    await session.refresh(video, ["watermark_regions"])
    for region in video.watermark_regions:
        print(region)
```

### 5. 级联删除

删除视频时，相关的水印区域和处理任务会自动删除：

```python
async with AsyncSessionLocal() as session:
    result = await session.execute(
        select(Video).where(Video.video_id == "vid_123")
    )
    video = result.scalar_one()
    
    # 删除视频，关联的 watermark_regions 和 processing_tasks 会自动删除
    await session.delete(video)
    await session.commit()
```

## 数据库文件位置

- 开发环境: `backend/video_platform.db`
- 可通过环境变量 `DATABASE_URL` 配置

## 测试

运行数据库测试：

```bash
cd backend
python test_database.py
```

运行应用启动测试：

```bash
cd backend
python test_app_startup.py
```

## 注意事项

1. **异步操作**: 所有数据库操作都是异步的，必须使用 `await` 关键字
2. **会话管理**: 使用 `async with` 确保会话正确关闭
3. **事务处理**: 修改操作后需要调用 `await session.commit()`
4. **错误处理**: 发生错误时会自动回滚事务
5. **级联删除**: 删除父记录时，子记录会自动删除（ON DELETE CASCADE）
6. **索引优化**: 已为常用查询字段创建索引，提升查询性能

## 性能优化建议

1. 使用索引加速查询
2. 批量操作使用事务
3. 避免 N+1 查询问题（使用 joinedload 或 selectinload）
4. 定期清理过期数据
5. 监控慢查询并优化

## 未来扩展

如果需要更强大的功能，可以考虑：

1. 迁移到 PostgreSQL（支持更复杂的查询和并发）
2. 添加数据库迁移工具（Alembic）
3. 实现读写分离
4. 添加缓存层（Redis）
5. 实现数据库备份和恢复机制
