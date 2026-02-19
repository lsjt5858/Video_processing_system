"""
API端点集成测试
"""
import pytest
import io
from pathlib import Path
from starlette.testclient import TestClient as StarletteTestClient

# 添加app目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    with StarletteTestClient(app) as c:
        yield c


@pytest.fixture
def test_video_path():
    """获取测试视频文件路径"""
    return Path(__file__).parent / "test_videos" / "test_video.mp4"


def get_real_video_content(test_video_path: Path) -> bytes:
    """读取真实的测试视频内容"""
    if test_video_path.exists():
        with open(test_video_path, "rb") as f:
            return f.read()
    # 如果测试视频不存在，跳过测试
    pytest.skip("测试视频文件不存在")


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "upload_dir" in data


def test_root_endpoint(client):
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_upload_single_video_mp4(client, test_video_path):
    """测试上传单个MP4视频"""
    # 使用真实的测试视频
    content = get_real_video_content(test_video_path)
    files = {
        "file": ("test_video.mp4", io.BytesIO(content), "video/mp4")
    }
    
    response = client.post("/api/videos/upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "video_id" in data["data"]
    assert data["data"]["format"] == "mp4"
    
    # 清理测试文件
    storage_path = Path(data["data"]["storage_path"])
    if storage_path.exists():
        storage_path.unlink()


def test_upload_single_video_avi(client, test_video_path):
    """测试上传AVI格式视频"""
    # 使用真实的测试视频（重命名为.avi）
    content = get_real_video_content(test_video_path)
    files = {
        "file": ("test_video.avi", io.BytesIO(content), "video/x-msvideo")
    }
    
    response = client.post("/api/videos/upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["format"] == "avi"
    
    # 清理测试文件
    storage_path = Path(data["data"]["storage_path"])
    if storage_path.exists():
        storage_path.unlink()


def test_upload_single_video_mov(client, test_video_path):
    """测试上传MOV格式视频"""
    # 使用真实的测试视频（重命名为.mov）
    content = get_real_video_content(test_video_path)
    files = {
        "file": ("test_video.mov", io.BytesIO(content), "video/quicktime")
    }
    
    response = client.post("/api/videos/upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["format"] == "mov"
    
    # 清理测试文件
    storage_path = Path(data["data"]["storage_path"])
    if storage_path.exists():
        storage_path.unlink()


def test_upload_single_video_mkv(client, test_video_path):
    """测试上传MKV格式视频"""
    # 使用真实的测试视频（重命名为.mkv）
    content = get_real_video_content(test_video_path)
    files = {
        "file": ("test_video.mkv", io.BytesIO(content), "video/x-matroska")
    }
    
    response = client.post("/api/videos/upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["format"] == "mkv"
    
    # 清理测试文件
    storage_path = Path(data["data"]["storage_path"])
    if storage_path.exists():
        storage_path.unlink()


def test_upload_unsupported_format(client):
    """测试上传不支持的格式"""
    content = b"fake video content"
    files = {
        "file": ("test_video.wmv", io.BytesIO(content), "video/x-ms-wmv")
    }
    
    response = client.post("/api/videos/upload", files=files)
    assert response.status_code == 415  # Unsupported Media Type


def test_upload_batch_videos(client, test_video_path):
    """测试批量上传视频"""
    # 使用真实的测试视频
    content = get_real_video_content(test_video_path)
    files = [
        ("files", ("test1.mp4", io.BytesIO(content), "video/mp4")),
        ("files", ("test2.avi", io.BytesIO(content), "video/x-msvideo")),
        ("files", ("test3.mov", io.BytesIO(content), "video/quicktime")),
    ]
    
    response = client.post("/api/videos/batch-upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 3
    assert data["data"]["success_count"] == 3
    assert data["data"]["failed_count"] == 0
    
    # 清理测试文件
    for item in data["data"]["successful"]:
        storage_path = Path(item["storage_path"])
        if storage_path.exists():
            storage_path.unlink()


def test_upload_batch_videos_mixed(client, test_video_path):
    """测试批量上传混合结果（部分成功，部分失败）"""
    # 使用真实的测试视频
    content = get_real_video_content(test_video_path)
    # 创建混合文件：2个有效，1个无效格式
    files = [
        ("files", ("test1.mp4", io.BytesIO(content), "video/mp4")),
        ("files", ("test2.wmv", io.BytesIO(b"fake content"), "video/x-ms-wmv")),  # 不支持
        ("files", ("test3.avi", io.BytesIO(content), "video/x-msvideo")),
    ]
    
    response = client.post("/api/videos/batch-upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 3
    assert data["data"]["success_count"] == 2
    assert data["data"]["failed_count"] == 1
    
    # 验证失败的文件
    assert len(data["data"]["failed"]) == 1
    assert data["data"]["failed"][0]["filename"] == "test2.wmv"
    
    # 清理测试文件
    for item in data["data"]["successful"]:
        storage_path = Path(item["storage_path"])
        if storage_path.exists():
            storage_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
