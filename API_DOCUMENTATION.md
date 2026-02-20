# API 文档 / API Documentation

视频水印去除工具的完整API文档。

## 基础信息 / Base Information

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **Content-Type**: `application/json`
- **WebSocket URL**: `ws://localhost:8000/ws/{client_id}`

## 认证 / Authentication

当前版本不需要认证。生产环境建议添加JWT认证。

## 错误响应格式 / Error Response Format

所有错误响应遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

常见HTTP状态码：
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `413`: 文件过大
- `422`: 验证错误
- `500`: 服务器内部错误

---

## 视频管理 API / Video Management API

### 1. 上传视频 / Upload Video

上传单个视频文件。

**端点**: `POST /api/videos/upload`

**请求**:
- Content-Type: `multipart/form-data`
- Body:
  - `file`: 视频文件（必需）

**响应**:
```json
{
  "video_id": "uuid",
  "filename": "video.mp4",
  "format": "mp4",
  "resolution": "1920x1080",
  "duration": 120.5,
  "codec": "h264",
  "framerate": 30.0,
  "bitrate": 5000000,
  "file_size": 150000000,
  "storage_path": "uploads/uuid.mp4",
  "created_at": "2024-01-15T10:30:00"
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@video.mp4"
```

---

### 2. 批量上传视频 / Batch Upload Videos

批量上传多个视频文件（最多50个）。

**端点**: `POST /api/videos/batch-upload`

**请求**:
- Content-Type: `multipart/form-data`
- Body:
  - `files`: 多个视频文件（必需）

**响应**:
```json
{
  "total": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "filename": "video1.mp4",
      "status": "success",
      "video_id": "uuid1",
      "message": "上传成功"
    },
    {
      "filename": "video2.mp4",
      "status": "success",
      "video_id": "uuid2",
      "message": "上传成功"
    },
    {
      "filename": "video3.mp4",
      "status": "failed",
      "error": "文件格式不支持"
    }
  ]
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/videos/batch-upload" \
  -F "files=@video1.mp4" \
  -F "files=@video2.mp4" \
  -F "files=@video3.mp4"
```

---

### 3. URL下载视频 / Download Video from URL

通过URL下载视频。

**端点**: `POST /api/videos/download`

**请求**:
```json
{
  "url": "https://example.com/video.mp4"
}
```

**响应**:
```json
{
  "video_id": "uuid",
  "url": "https://example.com/video.mp4",
  "status": "downloading",
  "message": "视频下载已开始"
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/videos/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video.mp4"}'
```

**注意**: 下载进度通过WebSocket推送。

---

### 4. 获取视频列表 / Get Video List

获取所有视频列表，支持分页。

**端点**: `GET /api/videos`

**查询参数**:
- `skip`: 跳过的记录数（默认: 0）
- `limit`: 返回的记录数（默认: 20，最大: 100）

**响应**:
```json
{
  "total": 50,
  "skip": 0,
  "limit": 20,
  "videos": [
    {
      "video_id": "uuid",
      "filename": "video.mp4",
      "format": "mp4",
      "resolution": "1920x1080",
      "duration": 120.5,
      "file_size": 150000000,
      "created_at": "2024-01-15T10:30:00",
      "watermark_count": 2,
      "has_output": true
    }
  ]
}
```

**示例**:
```bash
curl "http://localhost:8000/api/videos?skip=0&limit=20"
```

---

### 5. 获取视频详情 / Get Video Details

获取单个视频的详细信息。

**端点**: `GET /api/videos/{video_id}`

**路径参数**:
- `video_id`: 视频ID（必需）

**响应**:
```json
{
  "video_id": "uuid",
  "filename": "video.mp4",
  "format": "mp4",
  "resolution": "1920x1080",
  "duration": 120.5,
  "codec": "h264",
  "framerate": 30.0,
  "bitrate": 5000000,
  "file_size": 150000000,
  "storage_path": "uploads/uuid.mp4",
  "created_at": "2024-01-15T10:30:00",
  "watermarks": [
    {
      "region_id": "uuid",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 50,
      "start_time": 0.0,
      "end_time": 120.5
    }
  ],
  "tasks": [
    {
      "task_id": "uuid",
      "task_type": "removal",
      "status": "completed",
      "created_at": "2024-01-15T10:35:00"
    }
  ]
}
```

**示例**:
```bash
curl "http://localhost:8000/api/videos/{video_id}"
```

---

### 6. 删除视频 / Delete Video

删除视频及其相关数据。

**端点**: `DELETE /api/videos/{video_id}`

**路径参数**:
- `video_id`: 视频ID（必需）

**响应**:
```json
{
  "message": "视频删除成功",
  "video_id": "uuid"
}
```

**示例**:
```bash
curl -X DELETE "http://localhost:8000/api/videos/{video_id}"
```

---

## 水印检测 API / Watermark Detection API

### 7. 获取视频帧 / Get Video Frames

获取视频的关键帧用于水印标记。

**端点**: `GET /api/videos/{video_id}/frames`

**路径参数**:
- `video_id`: 视频ID（必需）

**查询参数**:
- `count`: 提取的帧数（默认: 10）

**响应**:
```json
{
  "video_id": "uuid",
  "frames": [
    {
      "frame_number": 0,
      "timestamp": 0.0,
      "thumbnail_path": "/thumbnails/uuid_frame_0.jpg"
    },
    {
      "frame_number": 30,
      "timestamp": 1.0,
      "thumbnail_path": "/thumbnails/uuid_frame_30.jpg"
    }
  ]
}
```

**示例**:
```bash
curl "http://localhost:8000/api/videos/{video_id}/frames?count=10"
```

---

### 8. 标记水印区域 / Mark Watermark Region

手动标记视频中的水印区域。

**端点**: `POST /api/videos/{video_id}/watermarks`

**路径参数**:
- `video_id`: 视频ID（必需）

**请求**:
```json
{
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 50,
  "start_time": 0.0,
  "end_time": 120.5
}
```

**响应**:
```json
{
  "region_id": "uuid",
  "video_id": "uuid",
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 50,
  "start_time": 0.0,
  "end_time": 120.5,
  "created_at": "2024-01-15T10:40:00"
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/videos/{video_id}/watermarks" \
  -H "Content-Type: application/json" \
  -d '{
    "x": 100,
    "y": 100,
    "width": 200,
    "height": 50,
    "start_time": 0.0,
    "end_time": 120.5
  }'
```

---

### 9. 获取水印列表 / Get Watermark List

获取视频的所有水印区域。

**端点**: `GET /api/videos/{video_id}/watermarks`

**路径参数**:
- `video_id`: 视频ID（必需）

**响应**:
```json
{
  "video_id": "uuid",
  "watermarks": [
    {
      "region_id": "uuid1",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 50,
      "start_time": 0.0,
      "end_time": 120.5
    },
    {
      "region_id": "uuid2",
      "x": 1700,
      "y": 50,
      "width": 150,
      "height": 40,
      "start_time": 0.0,
      "end_time": 120.5
    }
  ]
}
```

**示例**:
```bash
curl "http://localhost:8000/api/videos/{video_id}/watermarks"
```

---

### 10. 更新水印区域 / Update Watermark Region

更新已标记的水印区域。

**端点**: `PUT /api/videos/{video_id}/watermarks/{region_id}`

**路径参数**:
- `video_id`: 视频ID（必需）
- `region_id`: 水印区域ID（必需）

**请求**:
```json
{
  "x": 120,
  "y": 120,
  "width": 220,
  "height": 60,
  "start_time": 0.0,
  "end_time": 120.5
}
```

**响应**:
```json
{
  "region_id": "uuid",
  "video_id": "uuid",
  "x": 120,
  "y": 120,
  "width": 220,
  "height": 60,
  "start_time": 0.0,
  "end_time": 120.5,
  "updated_at": "2024-01-15T10:45:00"
}
```

**示例**:
```bash
curl -X PUT "http://localhost:8000/api/videos/{video_id}/watermarks/{region_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "x": 120,
    "y": 120,
    "width": 220,
    "height": 60,
    "start_time": 0.0,
    "end_time": 120.5
  }'
```

---

### 11. 删除水印区域 / Delete Watermark Region

删除已标记的水印区域。

**端点**: `DELETE /api/videos/{video_id}/watermarks/{region_id}`

**路径参数**:
- `video_id`: 视频ID（必需）
- `region_id`: 水印区域ID（必需）

**响应**:
```json
{
  "message": "水印区域删除成功",
  "region_id": "uuid"
}
```

**示例**:
```bash
curl -X DELETE "http://localhost:8000/api/videos/{video_id}/watermarks/{region_id}"
```

---

### 12. 批量检测 / Batch Detection

批量提取多个视频的关键帧。

**端点**: `POST /api/batch/detect`

**请求**:
```json
{
  "video_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**响应**:
```json
{
  "batch_id": "uuid",
  "total": 3,
  "status": "processing",
  "results": [
    {
      "video_id": "uuid1",
      "status": "completed",
      "frame_count": 10
    },
    {
      "video_id": "uuid2",
      "status": "processing"
    },
    {
      "video_id": "uuid3",
      "status": "pending"
    }
  ]
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/batch/detect" \
  -H "Content-Type: application/json" \
  -d '{"video_ids": ["uuid1", "uuid2", "uuid3"]}'
```

---

## 水印去除 API / Watermark Removal API

### 13. 去除水印 / Remove Watermark

对单个视频执行水印去除。

**端点**: `POST /api/videos/{video_id}/remove`

**路径参数**:
- `video_id`: 视频ID（必需）

**请求**:
```json
{
  "mode": "crop",
  "regions": [
    {
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 50
    }
  ],
  "crop_params": {
    "target_width": 1720,
    "target_height": 1080
  }
}
```

**响应**:
```json
{
  "task_id": "uuid",
  "video_id": "uuid",
  "status": "processing",
  "message": "水印去除任务已创建"
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/videos/{video_id}/remove" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "crop",
    "regions": [{"x": 100, "y": 100, "width": 200, "height": 50}],
    "crop_params": {"target_width": 1720, "target_height": 1080}
  }'
```

**注意**: 处理进度通过WebSocket推送。

---

### 14. 批量去除 / Batch Removal

批量执行水印去除。

**端点**: `POST /api/batch/remove`

**请求**:
```json
{
  "tasks": [
    {
      "video_id": "uuid1",
      "mode": "crop",
      "regions": [{"x": 100, "y": 100, "width": 200, "height": 50}],
      "crop_params": {"target_width": 1720, "target_height": 1080}
    },
    {
      "video_id": "uuid2",
      "mode": "crop",
      "regions": [{"x": 1700, "y": 50, "width": 150, "height": 40}],
      "crop_params": {"target_width": 1720, "target_height": 1080}
    }
  ]
}
```

**响应**:
```json
{
  "batch_id": "uuid",
  "total": 2,
  "status": "processing",
  "task_ids": ["task_uuid1", "task_uuid2"]
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/batch/remove" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "video_id": "uuid1",
        "mode": "crop",
        "regions": [{"x": 100, "y": 100, "width": 200, "height": 50}],
        "crop_params": {"target_width": 1720, "target_height": 1080}
      }
    ]
  }'
```

---

## 任务管理 API / Task Management API

### 15. 获取任务状态 / Get Task Status

获取单个任务的状态和详情。

**端点**: `GET /api/tasks/{task_id}`

**路径参数**:
- `task_id`: 任务ID（必需）

**响应**:
```json
{
  "task_id": "uuid",
  "video_id": "uuid",
  "task_type": "removal",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-15T10:50:00",
  "started_at": "2024-01-15T10:50:05",
  "completed_at": "2024-01-15T10:52:30",
  "result": {
    "output_path": "outputs/uuid_output.mp4",
    "output_size": 140000000,
    "processing_time": 145.5
  },
  "error": null
}
```

**示例**:
```bash
curl "http://localhost:8000/api/tasks/{task_id}"
```

---

### 16. 获取任务列表 / Get Task List

获取所有任务列表。

**端点**: `GET /api/tasks`

**查询参数**:
- `skip`: 跳过的记录数（默认: 0）
- `limit`: 返回的记录数（默认: 20）
- `status`: 过滤状态（可选: pending, processing, completed, failed）

**响应**:
```json
{
  "total": 30,
  "skip": 0,
  "limit": 20,
  "tasks": [
    {
      "task_id": "uuid",
      "video_id": "uuid",
      "task_type": "removal",
      "status": "completed",
      "progress": 100,
      "created_at": "2024-01-15T10:50:00"
    }
  ]
}
```

**示例**:
```bash
curl "http://localhost:8000/api/tasks?skip=0&limit=20&status=completed"
```

---

### 17. 下载处理后的视频 / Download Processed Video

下载处理后的视频文件。

**端点**: `GET /api/videos/{video_id}/output`

**路径参数**:
- `video_id`: 视频ID（必需）

**响应**: 视频文件流

**示例**:
```bash
curl "http://localhost:8000/api/videos/{video_id}/output" -o output.mp4
```

---

## WebSocket API

### 18. WebSocket连接 / WebSocket Connection

建立WebSocket连接以接收实时更新。

**端点**: `WS /ws/{client_id}`

**路径参数**:
- `client_id`: 客户端唯一标识（必需）

**消息格式**:

#### 上传进度
```json
{
  "type": "upload_progress",
  "video_id": "uuid",
  "filename": "video.mp4",
  "progress": 45,
  "uploaded": 67500000,
  "total": 150000000
}
```

#### 下载进度
```json
{
  "type": "download_progress",
  "video_id": "uuid",
  "url": "https://example.com/video.mp4",
  "progress": 60,
  "downloaded": 90000000,
  "total": 150000000
}
```

#### 处理进度
```json
{
  "type": "processing_progress",
  "task_id": "uuid",
  "video_id": "uuid",
  "progress": 75,
  "status": "processing",
  "message": "正在处理视频..."
}
```

#### 任务完成
```json
{
  "type": "task_completed",
  "task_id": "uuid",
  "video_id": "uuid",
  "status": "completed",
  "result": {
    "output_path": "outputs/uuid_output.mp4",
    "output_size": 140000000
  }
}
```

#### 任务失败
```json
{
  "type": "task_failed",
  "task_id": "uuid",
  "video_id": "uuid",
  "status": "failed",
  "error": "处理失败: FFmpeg错误"
}
```

**JavaScript示例**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client-123');

ws.onopen = () => {
  console.log('WebSocket连接已建立');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
  
  switch(data.type) {
    case 'upload_progress':
      console.log(`上传进度: ${data.progress}%`);
      break;
    case 'processing_progress':
      console.log(`处理进度: ${data.progress}%`);
      break;
    case 'task_completed':
      console.log('任务完成!');
      break;
    case 'task_failed':
      console.error('任务失败:', data.error);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket连接已关闭');
};
```

---

## 健康检查 API / Health Check API

### 19. 健康检查 / Health Check

检查服务健康状态。

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00"
}
```

**示例**:
```bash
curl "http://localhost:8000/health"
```

---

## 速率限制 / Rate Limiting

当前版本没有速率限制。生产环境建议添加：

- 上传: 10次/分钟
- API调用: 100次/分钟
- WebSocket连接: 5个/客户端

---

## 最佳实践 / Best Practices

1. **文件上传**
   - 大文件建议使用分片上传
   - 上传前验证文件格式和大小
   - 使用WebSocket监听上传进度

2. **批量操作**
   - 批量上传不超过50个文件
   - 批量处理建议分批次执行
   - 监听WebSocket获取实时进度

3. **错误处理**
   - 捕获所有API错误
   - 实现重试机制（网络错误）
   - 显示友好的错误提示

4. **WebSocket**
   - 实现断线重连
   - 处理所有消息类型
   - 及时关闭不用的连接

5. **性能优化**
   - 使用分页加载视频列表
   - 缓存视频元数据
   - 压缩请求和响应数据

---

## 更新日志 / Changelog

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持视频上传、下载、水印标记和去除
- 支持批量处理
- WebSocket实时通信

---

## 📚 相关文档 / Related Documentation

- **[项目概述](./README.md)** - 了解项目功能和快速开始
- **[快速开始](./docs/QUICKSTART.md)** - 5分钟快速部署
- **[部署指南](./DEPLOYMENT.md)** - 完整部署和运维指南
- **[常见问题](./FAQ.md)** - 问题排查和解决方案
- **[后端文档](./docs/BACKEND_README.md)** - 后端架构和开发
- **[前端文档](./docs/FRONTEND_README.md)** - 前端架构和开发
- **[文档索引](./docs/INDEX.md)** - 所有文档导航

## 💬 支持 / Support

如有问题，请：
1. 查看 [FAQ.md](./FAQ.md) 常见问题解答
2. 查看 [DEPLOYMENT.md](./DEPLOYMENT.md) 故障排查部分
3. 搜索 GitHub Issues
4. 提交新的 Issue 到项目仓库
