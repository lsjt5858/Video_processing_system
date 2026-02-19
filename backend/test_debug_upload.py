"""
Debug upload test
"""
import io
from pathlib import Path
from starlette.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app

with TestClient(app) as client:
    content = b"fake video content" * 100
    files = {
        "file": ("test_video.mp4", io.BytesIO(content), "video/mp4")
    }
    
    response = client.post("/api/videos/upload", files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
