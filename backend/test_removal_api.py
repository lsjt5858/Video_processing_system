"""
测试水印去除API端点

测试以下端点:
- POST /api/videos/{video_id}/remove - 单个视频水印去除
- GET /api/tasks/{task_id} - 获取任务状态
- GET /api/tasks - 获取任务列表
"""

import pytest
import asyncio
import uuid
from pathlib import Path
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import crud


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

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
async def db_session():
    """创建测试数据库会话"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with TestSessionLocal() as session:
        yield session
    
    # 清理所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_video(db_session):
    """创建测试视频记录"""
    video_id = f"test_video_{uuid.uuid4().hex[:8]}"
    
    video = await crud.create_video(
        db=db_session,
        video_id=video_id,
        user_id="test_user",
        format="mp4",
        resolution_width=1920,
        resolution_height=1080,
        duration=10.0,
        codec="h264",
        framerate=30.0,
        bitrate=5000000,
        file_size=10485760,
        storage_path=f"/test/path/{video_id}.mp4",
        import_source="local"
    )
    
    await db_session.commit()
    return video


@pytest.fixture
async def test_task(db_session, test_video):
    """创建测试任务记录"""
    task_id = f"test_task_{uuid.uuid4().hex[:8]}"
    
    task = await crud.create_processing_task(
        db=db_session,
        task_id=task_id,
        user_id="test_user",
        video_id=test_video.video_id,
        task_type="removal",
        status="pending",
        parameters={
            "mode": "crop_reconstruct",
            "regions": []
        }
    )
    
    await db_session.commit()
    return task


@pytest.mark.asyncio
async def test_single_video_removal_endpoint(db_session, test_video):
    """测试单个视频水印去除端点"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 准备请求数据
        request_data = {
            "regions": [
                {
                    "bbox": {"x": 10, "y": 10, "width": 100, "height": 50},
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "watermark_type": "manual"
                }
            ],
            "mode": "crop_reconstruct",
            "user_id": "test_user"
        }
        
        # 发送请求
        response = await client.post(
            f"/api/videos/{test_video.video_id}/remove",
            json=request_data
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data["data"]
        assert data["data"]["video_id"] == test_video.video_id
        assert data["data"]["status"] == "pending"
        
        # 验证任务已创建
        task_id = data["data"]["task_id"]
        task = await crud.get_task_by_id(db_session, task_id)
        assert task is not None
        assert task.video_id == test_video.video_id
        assert task.task_type == "removal"
        assert task.status == "pending"


@pytest.mark.asyncio
async def test_single_video_removal_invalid_video(db_session):
    """测试不存在的视频ID"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        request_data = {
            "regions": [],
            "mode": "crop_reconstruct",
            "user_id": "test_user"
        }
        
        response = await client.post(
            "/api/videos/nonexistent_video/remove",
            json=request_data
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_single_video_removal_invalid_mode(db_session, test_video):
    """测试无效的处理模式"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        request_data = {
            "regions": [],
            "mode": "invalid_mode",
            "user_id": "test_user"
        }
        
        response = await client.post(
            f"/api/videos/{test_video.video_id}/remove",
            json=request_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "无效的处理模式" in data["detail"]


@pytest.mark.asyncio
async def test_get_task_status_endpoint(db_session, test_task):
    """测试获取任务状态端点"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/tasks/{test_task.task_id}")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["task_id"] == test_task.task_id
        assert data["data"]["video_id"] == test_task.video_id
        assert data["data"]["task_type"] == "removal"
        assert data["data"]["status"] == "pending"
        assert "video" in data["data"]


@pytest.mark.asyncio
async def test_get_task_status_nonexistent(db_session):
    """测试获取不存在的任务"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/tasks/nonexistent_task")
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_get_tasks_list_endpoint(db_session, test_task):
    """测试获取任务列表端点"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/tasks")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tasks" in data["data"]
        assert "pagination" in data["data"]
        assert len(data["data"]["tasks"]) > 0
        
        # 验证分页信息
        pagination = data["data"]["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 20
        assert pagination["total_count"] >= 1


@pytest.mark.asyncio
async def test_get_tasks_list_with_filters(db_session, test_task):
    """测试带过滤条件的任务列表"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 测试用户过滤
        response = await client.get("/api/tasks?user_id=test_user")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["tasks"]) > 0
        
        # 测试状态过滤
        response = await client.get("/api/tasks?task_status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 测试任务类型过滤
        response = await client.get("/api/tasks?task_type=removal")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 测试组合过滤
        response = await client.get(
            "/api/tasks?user_id=test_user&task_status=pending&task_type=removal"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_get_tasks_list_pagination(db_session, test_video):
    """测试任务列表分页"""
    # 创建多个任务
    for i in range(5):
        task_id = f"test_task_{i}_{uuid.uuid4().hex[:8]}"
        await crud.create_processing_task(
            db=db_session,
            task_id=task_id,
            user_id="test_user",
            video_id=test_video.video_id,
            task_type="removal",
            status="pending",
            parameters={}
        )
    await db_session.commit()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 测试第一页
        response = await client.get("/api/tasks?page=1&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["tasks"]) == 3
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["has_next"] is True
        
        # 测试第二页
        response = await client.get("/api/tasks?page=2&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["tasks"]) >= 2
        assert data["data"]["pagination"]["page"] == 2


@pytest.mark.asyncio
async def test_get_tasks_list_invalid_status(db_session):
    """测试无效的状态过滤"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/tasks?task_status=invalid_status")
        
        assert response.status_code == 400
        data = response.json()
        assert "无效的状态" in data["detail"]


@pytest.mark.asyncio
async def test_get_tasks_list_invalid_task_type(db_session):
    """测试无效的任务类型过滤"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/tasks?task_type=invalid_type")
        
        assert response.status_code == 400
        data = response.json()
        assert "无效的任务类型" in data["detail"]


@pytest.mark.asyncio
async def test_get_tasks_list_invalid_pagination(db_session):
    """测试无效的分页参数"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 测试无效的页码
        response = await client.get("/api/tasks?page=0")
        assert response.status_code == 400
        
        # 测试无效的页面大小
        response = await client.get("/api/tasks?page_size=0")
        assert response.status_code == 400
        
        response = await client.get("/api/tasks?page_size=101")
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_task_with_completed_status(db_session, test_video):
    """测试已完成任务的状态查询"""
    # 创建已完成的任务
    task_id = f"completed_task_{uuid.uuid4().hex[:8]}"
    task = await crud.create_processing_task(
        db=db_session,
        task_id=task_id,
        user_id="test_user",
        video_id=test_video.video_id,
        task_type="removal",
        status="completed",
        parameters={"mode": "crop_reconstruct"}
    )
    
    # 更新任务结果
    from datetime import datetime
    await crud.update_task_status(
        db=db_session,
        task_id=task_id,
        status="completed",
        completed_at=datetime.now(),
        result={
            "output_video_id": "output_123",
            "output_path": "/test/output/output_123.mp4",
            "processing_mode": "crop_reconstruct"
        }
    )
    await db_session.commit()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "completed"
        assert data["data"]["result"] is not None
        assert "output_path" in data["data"]["result"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
