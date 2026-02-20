"""
测试视频列表、详情和删除API端点

测试Task 6.1中新增的三个端点:
- GET /api/videos - 获取视频列表（支持分页）
- GET /api/videos/{video_id} - 获取视频详情
- DELETE /api/videos/{video_id} - 删除视频
"""

import pytest
import asyncio
import os
from pathlib import Path
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event

# 导入应用和数据库模型
from app.main import app
from app.database import Base, get_db, init_db, close_db
from app import crud

# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_video_list.db"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# 启用SQLite外键支持
@event.listens_for(test_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# 创建测试会话工厂
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db():
    """覆盖数据库依赖"""
    async with TestSessionLocal() as session:
        yield session


# 覆盖应用的数据库依赖
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
async def test_db():
    """创建测试数据库"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理：删除所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def sample_videos(test_db):
    """创建示例视频数据"""
    async with TestSessionLocal() as db:
        videos = []
        
        # 创建5个测试视频
        for i in range(5):
            video = await crud.create_video(
                db=db,
                video_id=f"test_video_{i}",
                user_id="test_user",
                format="mp4",
                resolution_width=1920,
                resolution_height=1080,
                duration=120.0 + i * 10,
                codec="h264",
                framerate=30.0,
                bitrate=5000000,
                file_size=10485760 + i * 1000000,
                storage_path=f"/uploads/test_video_{i}.mp4",
                import_source="local"
            )
            videos.append(video)
        
        await db.commit()
        return videos


@pytest.mark.asyncio
async def test_get_videos_list_default_pagination(client, sample_videos):
    """测试获取视频列表 - 默认分页参数"""
    response = await client.get("/api/videos")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data
    assert "videos" in data["data"]
    assert "pagination" in data["data"]
    
    # 验证分页信息
    pagination = data["data"]["pagination"]
    assert pagination["page"] == 1
    assert pagination["page_size"] == 20
    assert pagination["total_count"] == 5
    assert pagination["total_pages"] == 1
    assert pagination["has_next"] is False
    assert pagination["has_prev"] is False
    
    # 验证视频列表
    videos = data["data"]["videos"]
    assert len(videos) == 5
    
    # 验证视频数据结构
    video = videos[0]
    assert "video_id" in video
    assert "user_id" in video
    assert "format" in video
    assert "resolution" in video
    assert "duration" in video
    assert "codec" in video
    assert "framerate" in video
    assert "bitrate" in video
    assert "file_size" in video
    assert "storage_path" in video
    assert "import_source" in video
    assert "created_at" in video


@pytest.mark.asyncio
async def test_get_videos_list_custom_pagination(client, sample_videos):
    """测试获取视频列表 - 自定义分页参数"""
    # 第1页，每页2条
    response = await client.get("/api/videos?page=1&page_size=2")
    
    assert response.status_code == 200
    data = response.json()
    
    pagination = data["data"]["pagination"]
    assert pagination["page"] == 1
    assert pagination["page_size"] == 2
    assert pagination["total_count"] == 5
    assert pagination["total_pages"] == 3
    assert pagination["has_next"] is True
    assert pagination["has_prev"] is False
    
    videos = data["data"]["videos"]
    assert len(videos) == 2
    
    # 第2页，每页2条
    response = await client.get("/api/videos?page=2&page_size=2")
    
    assert response.status_code == 200
    data = response.json()
    
    pagination = data["data"]["pagination"]
    assert pagination["page"] == 2
    assert pagination["has_next"] is True
    assert pagination["has_prev"] is True
    
    videos = data["data"]["videos"]
    assert len(videos) == 2
    
    # 第3页，每页2条（最后一页只有1条）
    response = await client.get("/api/videos?page=3&page_size=2")
    
    assert response.status_code == 200
    data = response.json()
    
    pagination = data["data"]["pagination"]
    assert pagination["page"] == 3
    assert pagination["has_next"] is False
    assert pagination["has_prev"] is True
    
    videos = data["data"]["videos"]
    assert len(videos) == 1


@pytest.mark.asyncio
async def test_get_videos_list_by_user(client, sample_videos):
    """测试获取视频列表 - 按用户筛选"""
    # 创建另一个用户的视频
    async with TestSessionLocal() as db:
        await crud.create_video(
            db=db,
            video_id="other_user_video",
            user_id="other_user",
            format="mp4",
            resolution_width=1280,
            resolution_height=720,
            duration=60.0,
            codec="h264",
            framerate=30.0,
            bitrate=3000000,
            file_size=5242880,
            storage_path="/uploads/other_user_video.mp4",
            import_source="url"
        )
        await db.commit()
    
    # 获取test_user的视频
    response = await client.get("/api/videos?user_id=test_user")
    
    assert response.status_code == 200
    data = response.json()
    
    videos = data["data"]["videos"]
    assert len(videos) == 5
    assert all(v["user_id"] == "test_user" for v in videos)
    
    # 获取other_user的视频
    response = await client.get("/api/videos?user_id=other_user")
    
    assert response.status_code == 200
    data = response.json()
    
    videos = data["data"]["videos"]
    assert len(videos) == 1
    assert videos[0]["user_id"] == "other_user"


@pytest.mark.asyncio
async def test_get_videos_list_invalid_page(client, sample_videos):
    """测试获取视频列表 - 无效的页码"""
    response = await client.get("/api/videos?page=0")
    
    assert response.status_code == 400
    data = response.json()
    assert "页码必须大于等于1" in data["detail"]


@pytest.mark.asyncio
async def test_get_videos_list_invalid_page_size(client, sample_videos):
    """测试获取视频列表 - 无效的每页数量"""
    # 每页数量小于1
    response = await client.get("/api/videos?page_size=0")
    assert response.status_code == 400
    
    # 每页数量大于100
    response = await client.get("/api/videos?page_size=101")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_video_details(client, sample_videos):
    """测试获取视频详情"""
    video_id = sample_videos[0].video_id
    
    # 添加水印区域
    async with TestSessionLocal() as db:
        await crud.create_watermark_region(
            db=db,
            region_id="test_region_1",
            video_id=video_id,
            bbox_x=100,
            bbox_y=50,
            bbox_width=200,
            bbox_height=100,
            start_time=0.0,
            end_time=120.0,
            confidence=0.95,
            watermark_type="corner",
            detection_method="manual"
        )
        
        # 添加处理任务
        await crud.create_processing_task(
            db=db,
            task_id="test_task_1",
            user_id="test_user",
            video_id=video_id,
            task_type="removal",
            status="completed",
            parameters={"mode": "crop_reconstruct"}
        )
        
        await db.commit()
    
    # 获取视频详情
    response = await client.get(f"/api/videos/{video_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data
    
    video_data = data["data"]
    assert video_data["video_id"] == video_id
    assert video_data["user_id"] == "test_user"
    assert video_data["format"] == "mp4"
    assert video_data["resolution"]["width"] == 1920
    assert video_data["resolution"]["height"] == 1080
    
    # 验证水印区域
    assert "watermark_regions" in video_data
    assert len(video_data["watermark_regions"]) == 1
    region = video_data["watermark_regions"][0]
    assert region["region_id"] == "test_region_1"
    assert region["bbox"]["x"] == 100
    assert region["bbox"]["y"] == 50
    assert region["watermark_type"] == "corner"
    
    # 验证处理任务
    assert "processing_tasks" in video_data
    assert len(video_data["processing_tasks"]) == 1
    task = video_data["processing_tasks"][0]
    assert task["task_id"] == "test_task_1"
    assert task["task_type"] == "removal"
    assert task["status"] == "completed"


@pytest.mark.asyncio
async def test_get_video_details_not_found(client, test_db):
    """测试获取不存在的视频详情"""
    response = await client.get("/api/videos/nonexistent_video")
    
    assert response.status_code == 404
    data = response.json()
    assert "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_delete_video(client, sample_videos):
    """测试删除视频"""
    video_id = sample_videos[0].video_id
    
    # 删除视频
    response = await client.delete(f"/api/videos/{video_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["video_id"] == video_id
    assert "已成功删除" in data["data"]["message"]
    
    # 验证视频已被删除
    async with TestSessionLocal() as db:
        video = await crud.get_video_by_id(db, video_id)
        assert video is None


@pytest.mark.asyncio
async def test_delete_video_with_relations(client, sample_videos):
    """测试删除视频及其关联数据"""
    video_id = sample_videos[0].video_id
    
    # 添加水印区域和处理任务
    async with TestSessionLocal() as db:
        await crud.create_watermark_region(
            db=db,
            region_id="test_region_2",
            video_id=video_id,
            bbox_x=100,
            bbox_y=50,
            bbox_width=200,
            bbox_height=100,
            start_time=0.0,
            end_time=120.0,
            confidence=0.95,
            watermark_type="corner",
            detection_method="manual"
        )
        
        await crud.create_processing_task(
            db=db,
            task_id="test_task_2",
            user_id="test_user",
            video_id=video_id,
            task_type="removal",
            status="completed",
            parameters={"mode": "crop_reconstruct"}
        )
        
        await db.commit()
    
    # 验证数据已创建
    async with TestSessionLocal() as db:
        regions_before = await crud.get_watermark_regions_by_video(db, video_id)
        tasks_before = await crud.get_tasks_by_video(db, video_id)
        assert len(regions_before) == 1
        assert len(tasks_before) == 1
    
    # 删除视频
    response = await client.delete(f"/api/videos/{video_id}")
    
    assert response.status_code == 200
    
    # 验证视频和关联数据都已被删除（级联删除）
    async with TestSessionLocal() as db:
        video = await crud.get_video_by_id(db, video_id)
        assert video is None
        
        # 注意：由于SQLite的外键约束，级联删除应该自动执行
        # 但在某些情况下可能需要显式启用外键支持
        regions = await crud.get_watermark_regions_by_video(db, video_id)
        tasks = await crud.get_tasks_by_video(db, video_id)
        
        # 如果级联删除正常工作，这些应该为空
        # 如果不为空，说明需要在数据库连接时启用外键支持
        assert len(regions) == 0, f"Expected 0 regions, but found {len(regions)}"
        assert len(tasks) == 0, f"Expected 0 tasks, but found {len(tasks)}"


@pytest.mark.asyncio
async def test_delete_video_not_found(client, test_db):
    """测试删除不存在的视频"""
    response = await client.delete("/api/videos/nonexistent_video")
    
    assert response.status_code == 404
    data = response.json()
    assert "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_get_videos_empty_list(client, test_db):
    """测试获取空视频列表"""
    response = await client.get("/api/videos")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]["videos"]) == 0
    assert data["data"]["pagination"]["total_count"] == 0
    assert data["data"]["pagination"]["total_pages"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
