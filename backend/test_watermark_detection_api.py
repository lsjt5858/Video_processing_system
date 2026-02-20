"""
测试水印检测API端点

测试以下端点:
- GET /api/videos/{video_id}/frames - 获取视频帧
- POST /api/videos/{video_id}/watermarks - 标记水印区域
- GET /api/videos/{video_id}/watermarks - 获取水印区域列表
- PUT /api/videos/{video_id}/watermarks/{region_id} - 更新水印区域
- DELETE /api/videos/{video_id}/watermarks/{region_id} - 删除水印区域
"""

import pytest
import os
import shutil
from pathlib import Path
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 导入应用和数据库模型
from app.main import app
from app.database import Base, get_db
from app import crud


# 测试数据库配置
TEST_DB_PATH = "test_watermark_api.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

# 测试目录
TEST_UPLOAD_DIR = Path("test_uploads_watermark_api")
TEST_OUTPUT_DIR = Path("test_outputs_watermark_api")
TEST_THUMBNAIL_DIR = Path("test_thumbnails_watermark_api")


@pytest.fixture(scope="function")
async def test_db():
    """创建测试数据库"""
    # 创建测试引擎
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话工厂
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # 提供会话
    async with async_session() as session:
        yield session
    
    # 清理
    await engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
async def client(test_db):
    """创建测试客户端"""
    # 覆盖数据库依赖
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # 创建测试目录
    TEST_UPLOAD_DIR.mkdir(exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    TEST_THUMBNAIL_DIR.mkdir(exist_ok=True)
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # 清理
    app.dependency_overrides.clear()
    
    # 删除测试目录
    if TEST_UPLOAD_DIR.exists():
        shutil.rmtree(TEST_UPLOAD_DIR)
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)
    if TEST_THUMBNAIL_DIR.exists():
        shutil.rmtree(TEST_THUMBNAIL_DIR)


@pytest.fixture
async def sample_video(test_db):
    """创建示例视频记录"""
    # 创建测试视频文件
    test_video_path = TEST_UPLOAD_DIR / "test_video.mp4"
    
    # 使用FFmpeg创建一个简单的测试视频（5秒，640x480）
    import subprocess
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=5:size=640x480:rate=30",
        "-pix_fmt", "yuv420p", "-y", str(test_video_path)
    ], capture_output=True)
    
    # 创建视频记录
    video = await crud.create_video(
        db=test_db,
        video_id="test_video_001",
        user_id="test_user",
        format="mp4",
        resolution_width=640,
        resolution_height=480,
        duration=5.0,
        codec="h264",
        framerate=30.0,
        bitrate=500000,
        file_size=os.path.getsize(test_video_path),
        storage_path=str(test_video_path),
        import_source="local"
    )
    
    await test_db.commit()
    
    return video


@pytest.mark.asyncio
async def test_get_video_frames_success(client, sample_video):
    """测试成功获取视频帧"""
    response = await client.get(f"/api/videos/{sample_video.video_id}/frames?num_frames=5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["video_id"] == sample_video.video_id
    assert data["data"]["num_frames"] == 5
    assert len(data["data"]["frames"]) == 5
    
    # 验证帧信息结构
    for frame in data["data"]["frames"]:
        assert "frame_index" in frame
        assert "timestamp" in frame
        assert "thumbnail_url" in frame
        assert frame["thumbnail_url"].startswith("/thumbnails/")


@pytest.mark.asyncio
async def test_get_video_frames_default_num(client, sample_video):
    """测试使用默认帧数获取视频帧"""
    response = await client.get(f"/api/videos/{sample_video.video_id}/frames")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["num_frames"] == 10  # 默认值


@pytest.mark.asyncio
async def test_get_video_frames_not_found(client):
    """测试获取不存在的视频的帧"""
    response = await client.get("/api/videos/nonexistent_video/frames")
    
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_mark_video_watermarks_success(client, sample_video, test_db):
    """测试成功标记水印区域"""
    request_data = {
        "bounding_boxes": [
            {
                "x": 10,
                "y": 10,
                "width": 100,
                "height": 50,
                "start_time": 0.0,
                "end_time": 5.0,
                "watermark_type": "corner"
            },
            {
                "x": 500,
                "y": 400,
                "width": 120,
                "height": 60,
                "start_time": 0.0,
                "end_time": 5.0,
                "watermark_type": "logo"
            }
        ]
    }
    
    response = await client.post(
        f"/api/videos/{sample_video.video_id}/watermarks",
        json=request_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["video_id"] == sample_video.video_id
    assert data["data"]["count"] == 2
    assert len(data["data"]["regions"]) == 2
    
    # 验证区域信息
    for region in data["data"]["regions"]:
        assert "region_id" in region
        assert "bbox" in region
        assert region["bbox"]["x"] >= 0
        assert region["bbox"]["y"] >= 0
        assert region["bbox"]["width"] > 0
        assert region["bbox"]["height"] > 0
        assert region["detection_method"] == "manual"
        assert region["confidence"] == 1.0


@pytest.mark.asyncio
async def test_mark_video_watermarks_invalid_bbox(client, sample_video):
    """测试标记无效的边界框"""
    request_data = {
        "bounding_boxes": [
            {
                "x": -10,  # 负数坐标
                "y": 10,
                "width": 100,
                "height": 50,
                "start_time": 0.0,
                "end_time": 5.0,
                "watermark_type": "corner"
            }
        ]
    }
    
    response = await client.post(
        f"/api/videos/{sample_video.video_id}/watermarks",
        json=request_data
    )
    
    assert response.status_code == 400
    # Pydantic validation error or custom validation error
    detail = response.json()["detail"]
    assert "无效" in detail or "validation error" in detail or "greater than or equal to 0" in detail


@pytest.mark.asyncio
async def test_mark_video_watermarks_out_of_bounds(client, sample_video):
    """测试标记超出视频范围的边界框"""
    request_data = {
        "bounding_boxes": [
            {
                "x": 600,
                "y": 450,
                "width": 100,  # 超出640x480的范围
                "height": 50,
                "start_time": 0.0,
                "end_time": 5.0,
                "watermark_type": "corner"
            }
        ]
    }
    
    response = await client.post(
        f"/api/videos/{sample_video.video_id}/watermarks",
        json=request_data
    )
    
    assert response.status_code == 400
    assert "无效" in response.json()["detail"]


@pytest.mark.asyncio
async def test_mark_video_watermarks_not_found(client):
    """测试标记不存在的视频"""
    request_data = {
        "bounding_boxes": [
            {
                "x": 10,
                "y": 10,
                "width": 100,
                "height": 50,
                "start_time": 0.0,
                "end_time": 5.0,
                "watermark_type": "corner"
            }
        ]
    }
    
    response = await client.post(
        "/api/videos/nonexistent_video/watermarks",
        json=request_data
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_video_watermarks_success(client, sample_video, test_db):
    """测试成功获取水印区域列表"""
    # 先创建一些水印区域
    await crud.create_watermark_region(
        db=test_db,
        region_id="region_001",
        video_id=sample_video.video_id,
        bbox_x=10,
        bbox_y=10,
        bbox_width=100,
        bbox_height=50,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="corner",
        detection_method="manual"
    )
    
    await crud.create_watermark_region(
        db=test_db,
        region_id="region_002",
        video_id=sample_video.video_id,
        bbox_x=500,
        bbox_y=400,
        bbox_width=120,
        bbox_height=60,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="logo",
        detection_method="manual"
    )
    
    await test_db.commit()
    
    # 获取水印区域列表
    response = await client.get(f"/api/videos/{sample_video.video_id}/watermarks")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["video_id"] == sample_video.video_id
    assert data["data"]["count"] == 2
    assert len(data["data"]["regions"]) == 2


@pytest.mark.asyncio
async def test_get_video_watermarks_empty(client, sample_video):
    """测试获取没有水印的视频"""
    response = await client.get(f"/api/videos/{sample_video.video_id}/watermarks")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["count"] == 0
    assert len(data["data"]["regions"]) == 0


@pytest.mark.asyncio
async def test_get_video_watermarks_not_found(client):
    """测试获取不存在的视频的水印"""
    response = await client.get("/api/videos/nonexistent_video/watermarks")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_video_watermark_bbox(client, sample_video, test_db):
    """测试更新水印区域的边界框"""
    # 创建水印区域
    region = await crud.create_watermark_region(
        db=test_db,
        region_id="region_001",
        video_id=sample_video.video_id,
        bbox_x=10,
        bbox_y=10,
        bbox_width=100,
        bbox_height=50,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="corner",
        detection_method="manual"
    )
    await test_db.commit()
    
    # 更新边界框
    update_data = {
        "bbox": {
            "x": 20,
            "y": 20,
            "width": 150,
            "height": 75
        }
    }
    
    response = await client.put(
        f"/api/videos/{sample_video.video_id}/watermarks/{region.region_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["bbox"]["x"] == 20
    assert data["data"]["bbox"]["y"] == 20
    assert data["data"]["bbox"]["width"] == 150
    assert data["data"]["bbox"]["height"] == 75


@pytest.mark.asyncio
async def test_update_video_watermark_time_range(client, sample_video, test_db):
    """测试更新水印区域的时间范围"""
    # 创建水印区域
    region = await crud.create_watermark_region(
        db=test_db,
        region_id="region_001",
        video_id=sample_video.video_id,
        bbox_x=10,
        bbox_y=10,
        bbox_width=100,
        bbox_height=50,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="corner",
        detection_method="manual"
    )
    await test_db.commit()
    
    # 更新时间范围
    update_data = {
        "start_time": 1.0,
        "end_time": 4.0
    }
    
    response = await client.put(
        f"/api/videos/{sample_video.video_id}/watermarks/{region.region_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["start_time"] == 1.0
    assert data["data"]["end_time"] == 4.0


@pytest.mark.asyncio
async def test_update_video_watermark_type(client, sample_video, test_db):
    """测试更新水印类型"""
    # 创建水印区域
    region = await crud.create_watermark_region(
        db=test_db,
        region_id="region_001",
        video_id=sample_video.video_id,
        bbox_x=10,
        bbox_y=10,
        bbox_width=100,
        bbox_height=50,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="corner",
        detection_method="manual"
    )
    await test_db.commit()
    
    # 更新水印类型
    update_data = {
        "watermark_type": "logo"
    }
    
    response = await client.put(
        f"/api/videos/{sample_video.video_id}/watermarks/{region.region_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["watermark_type"] == "logo"


@pytest.mark.asyncio
async def test_update_video_watermark_invalid_bbox(client, sample_video, test_db):
    """测试更新为无效的边界框"""
    # 创建水印区域
    region = await crud.create_watermark_region(
        db=test_db,
        region_id="region_001",
        video_id=sample_video.video_id,
        bbox_x=10,
        bbox_y=10,
        bbox_width=100,
        bbox_height=50,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="corner",
        detection_method="manual"
    )
    await test_db.commit()
    
    # 尝试更新为超出范围的边界框
    update_data = {
        "bbox": {
            "x": 600,
            "y": 450,
            "width": 100,
            "height": 50
        }
    }
    
    response = await client.put(
        f"/api/videos/{sample_video.video_id}/watermarks/{region.region_id}",
        json=update_data
    )
    
    assert response.status_code == 400
    assert "无效" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_video_watermark_not_found(client, sample_video):
    """测试更新不存在的水印区域"""
    update_data = {
        "bbox": {
            "x": 20,
            "y": 20,
            "width": 150,
            "height": 75
        }
    }
    
    response = await client.put(
        f"/api/videos/{sample_video.video_id}/watermarks/nonexistent_region",
        json=update_data
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_video_watermark_wrong_video(client, sample_video, test_db):
    """测试更新属于其他视频的水印区域"""
    # 创建另一个视频
    other_video = await crud.create_video(
        db=test_db,
        video_id="other_video_001",
        user_id="test_user",
        format="mp4",
        resolution_width=640,
        resolution_height=480,
        duration=5.0,
        codec="h264",
        framerate=30.0,
        bitrate=500000,
        file_size=1000000,
        storage_path="/path/to/other_video.mp4",
        import_source="local"
    )
    
    # 为另一个视频创建水印区域
    region = await crud.create_watermark_region(
        db=test_db,
        region_id="region_001",
        video_id=other_video.video_id,
        bbox_x=10,
        bbox_y=10,
        bbox_width=100,
        bbox_height=50,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="corner",
        detection_method="manual"
    )
    await test_db.commit()
    
    # 尝试用sample_video的ID更新other_video的水印区域
    update_data = {
        "bbox": {
            "x": 20,
            "y": 20,
            "width": 150,
            "height": 75
        }
    }
    
    response = await client.put(
        f"/api/videos/{sample_video.video_id}/watermarks/{region.region_id}",
        json=update_data
    )
    
    assert response.status_code == 400
    assert "不属于" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_video_watermark_success(client, sample_video, test_db):
    """测试成功删除水印区域"""
    # 创建水印区域
    region = await crud.create_watermark_region(
        db=test_db,
        region_id="region_001",
        video_id=sample_video.video_id,
        bbox_x=10,
        bbox_y=10,
        bbox_width=100,
        bbox_height=50,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="corner",
        detection_method="manual"
    )
    await test_db.commit()
    
    # 删除水印区域
    response = await client.delete(
        f"/api/videos/{sample_video.video_id}/watermarks/{region.region_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["region_id"] == region.region_id
    assert "成功删除" in data["data"]["message"]
    
    # 验证已删除
    deleted_region = await crud.get_watermark_region_by_id(test_db, region.region_id)
    assert deleted_region is None


@pytest.mark.asyncio
async def test_delete_video_watermark_not_found(client, sample_video):
    """测试删除不存在的水印区域"""
    response = await client.delete(
        f"/api/videos/{sample_video.video_id}/watermarks/nonexistent_region"
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_video_watermark_wrong_video(client, sample_video, test_db):
    """测试删除属于其他视频的水印区域"""
    # 创建另一个视频
    other_video = await crud.create_video(
        db=test_db,
        video_id="other_video_001",
        user_id="test_user",
        format="mp4",
        resolution_width=640,
        resolution_height=480,
        duration=5.0,
        codec="h264",
        framerate=30.0,
        bitrate=500000,
        file_size=1000000,
        storage_path="/path/to/other_video.mp4",
        import_source="local"
    )
    
    # 为另一个视频创建水印区域
    region = await crud.create_watermark_region(
        db=test_db,
        region_id="region_001",
        video_id=other_video.video_id,
        bbox_x=10,
        bbox_y=10,
        bbox_width=100,
        bbox_height=50,
        start_time=0.0,
        end_time=5.0,
        confidence=1.0,
        watermark_type="corner",
        detection_method="manual"
    )
    await test_db.commit()
    
    # 尝试用sample_video的ID删除other_video的水印区域
    response = await client.delete(
        f"/api/videos/{sample_video.video_id}/watermarks/{region.region_id}"
    )
    
    assert response.status_code == 400
    assert "不属于" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
