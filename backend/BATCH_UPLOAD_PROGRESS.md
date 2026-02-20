# 批量上传进度管理功能

## 概述

批量上传进度管理功能实现了以下特性：
1. **并发控制**：最多5个文件并行上传
2. **进度跟踪**：实时跟踪每个文件的上传状态
3. **WebSocket推送**：通过WebSocket实时推送进度更新
4. **错误隔离**：单个文件失败不影响其他文件

## API使用

### 端点

```
POST /api/videos/batch-upload
```

### 参数

- `files`: 视频文件列表（最多50个）
- `user_id`: 用户ID（可选，默认"default_user"）
- `client_id`: 客户端ID，用于WebSocket进度推送（可选）

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/videos/batch-upload?client_id=client123" \
  -F "files=@video1.mp4" \
  -F "files=@video2.mp4" \
  -F "files=@video3.mp4"
```

### 响应格式

```json
{
  "success": true,
  "data": {
    "total": 3,
    "success_count": 2,
    "failed_count": 1,
    "successful": [
      {
        "filename": "video1.mp4",
        "video_id": "uuid-1",
        "file_size": 1024000,
        "storage_path": "/uploads/uuid-1.mp4",
        "index": 0
      },
      {
        "filename": "video3.mp4",
        "video_id": "uuid-3",
        "file_size": 2048000,
        "storage_path": "/uploads/uuid-3.mp4",
        "index": 2
      }
    ],
    "failed": [
      {
        "filename": "video2.wmv",
        "error": "不支持的视频格式: .wmv",
        "index": 1
      }
    ]
  }
}
```

## WebSocket进度推送

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client123');
```

### 消息格式

#### 1. 上传开始消息

```json
{
  "type": "batch_upload_progress",
  "file_index": 0,
  "filename": "video1.mp4",
  "status": "uploading",
  "progress": 0,
  "completed": 0,
  "total": 3
}
```

#### 2. 上传完成消息

```json
{
  "type": "batch_upload_progress",
  "file_index": 0,
  "filename": "video1.mp4",
  "status": "completed",
  "progress": 100,
  "video_id": "uuid-1",
  "completed": 1,
  "total": 3
}
```

#### 3. 上传失败消息

```json
{
  "type": "batch_upload_progress",
  "file_index": 1,
  "filename": "video2.wmv",
  "status": "failed",
  "error": "不支持的视频格式: .wmv",
  "completed": 2,
  "total": 3
}
```

#### 4. 批量上传完成消息

```json
{
  "type": "batch_upload_complete",
  "total": 3,
  "success_count": 2,
  "failed_count": 1
}
```

## 前端集成示例

### React + WebSocket

```javascript
import { useState, useEffect } from 'react';

function BatchUpload() {
  const [progress, setProgress] = useState({});
  const [ws, setWs] = useState(null);
  const clientId = 'client-' + Date.now();

  useEffect(() => {
    // 建立WebSocket连接
    const websocket = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
    
    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'batch_upload_progress') {
        setProgress(prev => ({
          ...prev,
          [message.file_index]: {
            filename: message.filename,
            status: message.status,
            progress: message.progress,
            error: message.error,
            videoId: message.video_id
          }
        }));
      } else if (message.type === 'batch_upload_complete') {
        console.log('批量上传完成:', message);
      }
    };
    
    setWs(websocket);
    
    return () => websocket.close();
  }, []);

  const handleUpload = async (files) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await fetch(
      `http://localhost:8000/api/videos/batch-upload?client_id=${clientId}`,
      {
        method: 'POST',
        body: formData
      }
    );
    
    const result = await response.json();
    console.log('上传结果:', result);
  };

  return (
    <div>
      <input 
        type="file" 
        multiple 
        onChange={(e) => handleUpload(Array.from(e.target.files))}
      />
      
      <div>
        {Object.entries(progress).map(([index, info]) => (
          <div key={index}>
            <p>{info.filename}</p>
            <p>状态: {info.status}</p>
            {info.status === 'uploading' && (
              <progress value={info.progress} max="100" />
            )}
            {info.status === 'failed' && (
              <p style={{color: 'red'}}>错误: {info.error}</p>
            )}
            {info.status === 'completed' && (
              <p style={{color: 'green'}}>完成 (ID: {info.videoId})</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## 技术实现

### 并发控制

使用 `asyncio.Semaphore(5)` 限制最多5个文件并行上传：

```python
semaphore = asyncio.Semaphore(5)

async def upload_with_progress(file: UploadFile, index: int):
    async with semaphore:
        # 上传逻辑
        result = await upload_single_video(file, user_id)
```

### 进度跟踪

使用共享状态和锁来跟踪完成数量：

```python
completed_count = 0
lock = asyncio.Lock()

async with lock:
    completed_count += 1
```

### 错误隔离

每个文件的上传在独立的任务中执行，使用 try-except 捕获异常：

```python
try:
    result = await upload_single_video(file, user_id)
    results["successful"].append(...)
except Exception as e:
    results["failed"].append(...)
```

### 并发执行

使用 `asyncio.gather()` 并发执行所有上传任务：

```python
tasks = [upload_with_progress(file, i) for i, file in enumerate(files)]
await asyncio.gather(*tasks)
```

## 测试

运行测试：

```bash
cd backend
python -m pytest test_batch_upload_progress.py -v
```

测试覆盖：
- ✅ 并发限制（最多5个并行）
- ✅ 进度跟踪和WebSocket推送
- ✅ 错误隔离（单个失败不影响其他）
- ✅ 文件索引跟踪
- ✅ 最大文件数限制（50个）
- ✅ 无WebSocket时正常工作

## 性能特性

- **并发上传**：最多5个文件同时上传，提高吞吐量
- **实时反馈**：通过WebSocket实时推送进度，提升用户体验
- **容错性**：单个文件失败不影响其他文件，保证批量操作的可靠性
- **可扩展性**：支持最多50个文件的批量上传

## 注意事项

1. **WebSocket连接**：如果需要进度推送，必须先建立WebSocket连接
2. **client_id**：确保每个客户端使用唯一的client_id
3. **文件大小**：单个文件最大5GB
4. **文件格式**：支持MP4、AVI、MOV、MKV格式
5. **并发限制**：系统自动限制最多5个文件并行上传
