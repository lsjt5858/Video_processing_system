"""
测试视频下载端点

测试 GET /api/videos/{video_id}/output 端点的功能
"""

import pytest
import uuid
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, Video as DBVideo, ProcessingTask as DBProcessingTask


# 测试数据库设置
@pytest.fixture
async def test_db():
    """创建测试数据库"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def test_client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def test_output_dir(tmp_path):
    """创建临时输出目录"""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_output_video(test_output_dir):
    """创建示例输出视频文件"""
    output_video_id = f"output_{uuid.uuid4().hex[:12]}"
    output_path = test_output_dir / f"{output_video_id}.mp4"
    
    # 创建一个假的视频文件
    with open(output_path, "wb") as f:
        f.write(b"fake video content for testing")
    
    return {
        "output_video_id": output_video_id,
        "output_path": str(output_path)
    }


@pytest.fixture
async def sample_completed_task(test_db, sample_output_video):
    """创建已完成的处理任务"""
    video_id = f"vid_{uuid.uuid4().hex[:12]}"
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    
    # 创建视频记录
    video = DBVideo(
        video_id=video_id,
        user_id="test_user",
        format="mp4",
        resolution_width=1920,
        resolution_height=1080,
        duration=120.0,
        codec="h264",
        framerate=30.0,
        bitrate=5000000,
        file_size=104857600,
        storage_path="/fake/path/input.mp4",
        import_source="local",
        created_at=datetime.now()
    )
    test_db.add(video)
    
    # 创建已完成的处理任务
    task = DBProcessingTask(
        task_id=task_id,
        user_id="test_user",
        video_id=video_id,
        task_type="removal",
        status="completed",
        parameters={"mode": "crop_reconstruct"},
        created_at=datetime.now(),
        started_at=datetime.now(),
        completed_at=datetime.now(),
        result={
            "output_video_id": sample_output_video["output_video_id"],
            "output_path": sample_output_video["output_path"],
            "processing_mode": "crop_reconstruct",
            "processing_duration": 10.5,
            "parameters": {
                "crop_x": 0,
                "crop_y": 0,
                "crop_width": 1700,
                "crop_height": 1080,
                "content_integrity": 0.95
            }
        }
    )
    test_db.add(task)
    await test_db.commit()
    
    return {
        "video_id": video_id,
        "task_id": task_id,
        "output_video_id": sample_output_video["output_video_id"],
        "output_path": sample_output_video["output_path"]
    }


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


class TestVideoDownloadEndpoint:
    """测试视频下载端点"""
    
    @pytest.mark.asyncio
    async def test_download_output_video_success(self, test_client, test_db, sample_completed_task):
        """测试成功下载处理后的视频"""
        # Override the get_db dependency
        from app.main import app, get_db
        
        async def override_get_db():
            yield test_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 发送下载请求
            response = test_client.get(f"/api/videos/{sample_completed_task['video_id']}/output")
            
            # 验证响应
            assert response.status_code == 200
            assert response.headers["content-type"] == "video/mp4"
            assert "attachment" in response.headers["content-disposition"]
            assert sample_completed_task["output_video_id"] in response.headers["content-disposition"]
            
            # 验证文件内容
            assert response.content == b"fake video content for testing"
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_download_video_not_found(self, test_client, test_db):
        """测试下载不存在的视频"""
        from app.main import app, get_db
        
        async def override_get_db():
            yield test_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 发送下载请求（不存在的视频ID）
            response = test_client.get("/api/videos/nonexistent_video/output")
            
            # 验证响应
            assert response.status_code == 404
            assert "未找到视频" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_download_video_no_completed_task(self, test_client, test_db):
        """测试下载没有完成处理的视频"""
        from app.main import app, get_db
        
        # 创建视频但没有完成的任务
        video_id = f"vid_{uuid.uuid4().hex[:12]}"
        video = DBVideo(
            video_id=video_id,
            user_id="test_user",
            format="mp4",
            resolution_width=1920,
            resolution_height=1080,
            duration=120.0,
            codec="h264",
            framerate=30.0,
            bitrate=5000000,
            file_size=104857600,
            storage_path="/fake/path/input.mp4",
            import_source="local",
            created_at=datetime.now()
        )
        test_db.add(video)
        
        # 创建pending状态的任务
        task = DBProcessingTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            user_id="test_user",
            video_id=video_id,
            task_type="removal",
            status="pending",
            parameters={"mode": "crop_reconstruct"},
            created_at=datetime.now()
        )
        test_db.add(task)
        await test_db.commit()
        
        async def override_get_db():
            yield test_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 发送下载请求
            response = test_client.get(f"/api/videos/{video_id}/output")
            
            # 验证响应
            assert response.status_code == 404
            assert "未找到视频" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_download_video_file_not_exists(self, test_client, test_db):
        """测试下载输出文件不存在的情况"""
        from app.main import app, get_db
        
        video_id = f"vid_{uuid.uuid4().hex[:12]}"
        
        # 创建视频记录
        video = DBVideo(
            video_id=video_id,
            user_id="test_user",
            format="mp4",
            resolution_width=1920,
            resolution_height=1080,
            duration=120.0,
            codec="h264",
            framerate=30.0,
            bitrate=5000000,
            file_size=104857600,
            storage_path="/fake/path/input.mp4",
            import_source="local",
            created_at=datetime.now()
        )
        test_db.add(video)
        
        # 创建已完成的任务，但输出文件不存在
        task = DBProcessingTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            user_id="test_user",
            video_id=video_id,
            task_type="removal",
            status="completed",
            parameters={"mode": "crop_reconstruct"},
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            result={
                "output_video_id": "nonexistent_output",
                "output_path": "/nonexistent/path/output.mp4",
                "processing_mode": "crop_reconstruct",
                "processing_duration": 10.5
            }
        )
        test_db.add(task)
        await test_db.commit()
        
        async def override_get_db():
            yield test_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 发送下载请求
            response = test_client.get(f"/api/videos/{video_id}/output")
            
            # 验证响应
            assert response.status_code == 404
            assert "输出文件不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_download_video_no_output_path_in_result(self, test_client, test_db):
        """测试任务结果中没有output_path的情况"""
        from app.main import app, get_db
        
        video_id = f"vid_{uuid.uuid4().hex[:12]}"
        
        # 创建视频记录
        video = DBVideo(
            video_id=video_id,
            user_id="test_user",
            format="mp4",
            resolution_width=1920,
            resolution_height=1080,
            duration=120.0,
            codec="h264",
            framerate=30.0,
            bitrate=5000000,
            file_size=104857600,
            storage_path="/fake/path/input.mp4",
            import_source="local",
            created_at=datetime.now()
        )
        test_db.add(video)
        
        # 创建已完成的任务，但结果中没有output_path
        task = DBProcessingTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            user_id="test_user",
            video_id=video_id,
            task_type="removal",
            status="completed",
            parameters={"mode": "crop_reconstruct"},
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            result={
                "output_video_id": "output_123",
                # 缺少 output_path
                "processing_mode": "crop_reconstruct",
                "processing_duration": 10.5
            }
        )
        test_db.add(task)
        await test_db.commit()
        
        async def override_get_db():
            yield test_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 发送下载请求
            response = test_client.get(f"/api/videos/{video_id}/output")
            
            # 验证响应
            assert response.status_code == 404
            assert "未找到输出路径" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_download_latest_output_video(self, test_client, test_db, test_output_dir):
        """测试下载最新的处理结果（当有多个完成的任务时）"""
        from app.main import app, get_db
        
        video_id = f"vid_{uuid.uuid4().hex[:12]}"
        
        # 创建视频记录
        video = DBVideo(
            video_id=video_id,
            user_id="test_user",
            format="mp4",
            resolution_width=1920,
            resolution_height=1080,
            duration=120.0,
            codec="h264",
            framerate=30.0,
            bitrate=5000000,
            file_size=104857600,
            storage_path="/fake/path/input.mp4",
            import_source="local",
            created_at=datetime.now()
        )
        test_db.add(video)
        
        # 创建第一个输出文件（旧的）
        old_output_id = f"output_old_{uuid.uuid4().hex[:12]}"
        old_output_path = test_output_dir / f"{old_output_id}.mp4"
        with open(old_output_path, "wb") as f:
            f.write(b"old video content")
        
        # 创建第一个完成的任务（旧的）
        import time
        old_completed_at = datetime.now()
        old_task = DBProcessingTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            user_id="test_user",
            video_id=video_id,
            task_type="removal",
            status="completed",
            parameters={"mode": "crop_reconstruct"},
            created_at=old_completed_at,
            started_at=old_completed_at,
            completed_at=old_completed_at,
            result={
                "output_video_id": old_output_id,
                "output_path": str(old_output_path),
                "processing_mode": "crop_reconstruct",
                "processing_duration": 5.0
            }
        )
        test_db.add(old_task)
        await test_db.commit()
        
        # 等待一小段时间确保时间戳不同
        time.sleep(0.01)
        
        # 创建第二个输出文件（新的）
        new_output_id = f"output_new_{uuid.uuid4().hex[:12]}"
        new_output_path = test_output_dir / f"{new_output_id}.mp4"
        with open(new_output_path, "wb") as f:
            f.write(b"new video content")
        
        # 创建第二个完成的任务（新的）
        new_completed_at = datetime.now()
        new_task = DBProcessingTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            user_id="test_user",
            video_id=video_id,
            task_type="removal",
            status="completed",
            parameters={"mode": "crop_reconstruct"},
            created_at=new_completed_at,
            started_at=new_completed_at,
            completed_at=new_completed_at,
            result={
                "output_video_id": new_output_id,
                "output_path": str(new_output_path),
                "processing_mode": "crop_reconstruct",
                "processing_duration": 5.0
            }
        )
        test_db.add(new_task)
        await test_db.commit()
        
        async def override_get_db():
            yield test_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 发送下载请求
            response = test_client.get(f"/api/videos/{video_id}/output")
            
            # 验证响应 - 应该返回最新的输出
            if response.status_code != 200:
                print(f"Error response: {response.json()}")
            assert response.status_code == 200
            assert response.content == b"new video content"
            assert new_output_id in response.headers["content-disposition"]
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_download_video_with_correct_headers(self, test_client, test_db, sample_completed_task):
        """测试下载响应包含正确的HTTP头"""
        from app.main import app, get_db
        
        async def override_get_db():
            yield test_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 发送下载请求
            response = test_client.get(f"/api/videos/{sample_completed_task['video_id']}/output")
            
            # 验证响应头
            assert response.status_code == 200
            
            # 验证Content-Type
            assert response.headers["content-type"] == "video/mp4"
            
            # 验证Content-Disposition
            content_disposition = response.headers["content-disposition"]
            assert "attachment" in content_disposition
            assert "filename=" in content_disposition
            assert ".mp4" in content_disposition
            assert sample_completed_task["output_video_id"] in content_disposition
        finally:
            app.dependency_overrides.clear()


class TestVideoDownloadIntegration:
    """集成测试：测试完整的处理和下载流程"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_process_and_download(self, test_client, test_db, test_output_dir):
        """测试完整工作流：上传 -> 处理 -> 下载"""
        from app.main import app, get_db
        from unittest.mock import patch, MagicMock
        from app.models import ProcessingMode
        
        # 1. 创建视频记录（模拟上传）
        video_id = f"vid_{uuid.uuid4().hex[:12]}"
        video = DBVideo(
            video_id=video_id,
            user_id="test_user",
            format="mp4",
            resolution_width=1920,
            resolution_height=1080,
            duration=120.0,
            codec="h264",
            framerate=30.0,
            bitrate=5000000,
            file_size=104857600,
            storage_path="/fake/path/input.mp4",
            import_source="local",
            created_at=datetime.now()
        )
        test_db.add(video)
        await test_db.commit()
        
        # 2. 创建输出文件（模拟处理）
        output_video_id = f"output_{uuid.uuid4().hex[:12]}"
        output_path = test_output_dir / f"{output_video_id}.mp4"
        with open(output_path, "wb") as f:
            f.write(b"processed video content")
        
        # 3. 创建完成的处理任务
        task = DBProcessingTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            user_id="test_user",
            video_id=video_id,
            task_type="removal",
            status="completed",
            parameters={"mode": "crop_reconstruct"},
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            result={
                "output_video_id": output_video_id,
                "output_path": str(output_path),
                "processing_mode": "crop_reconstruct",
                "processing_duration": 10.5,
                "parameters": {
                    "crop_x": 0,
                    "crop_y": 0,
                    "crop_width": 1700,
                    "crop_height": 1080,
                    "content_integrity": 0.95
                }
            }
        )
        test_db.add(task)
        await test_db.commit()
        
        async def override_get_db():
            yield test_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 4. 下载处理后的视频
            response = test_client.get(f"/api/videos/{video_id}/output")
            
            # 5. 验证下载成功
            assert response.status_code == 200
            assert response.content == b"processed video content"
            assert response.headers["content-type"] == "video/mp4"
            assert output_video_id in response.headers["content-disposition"]
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
