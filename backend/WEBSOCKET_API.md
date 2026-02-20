# WebSocket API 文档

## 概述

本系统使用WebSocket实现实时进度推送功能，支持视频上传、下载、处理等操作的实时状态更新。

## 连接端点

```
WS /ws/{client_id}
```

### 参数

- `client_id` (string, required): 客户端唯一标识符，用于区分不同的客户端连接

### 连接示例

```javascript
// JavaScript/TypeScript
const ws = new WebSocket('ws://localhost:8000/ws/my_client_id');

ws.onopen = () => {
  console.log('WebSocket连接已建立');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket连接已关闭');
};
```

```python
# Python
import asyncio
import websockets
import json

async def connect_websocket():
    uri = "ws://localhost:8000/ws/my_client_id"
    async with websockets.connect(uri) as websocket:
        # 接收消息
        async for message in websocket:
            data = json.loads(message)
            print(f"收到消息: {data}")

asyncio.run(connect_websocket())
```

## 消息格式

所有WebSocket消息都是JSON格式，包含一个 `type` 字段用于标识消息类型。

### 通用字段

- `type` (string): 消息类型
- `message` (string, optional): 人类可读的消息描述

## 消息类型

### 1. 连接确认消息

**类型**: `pong`

**说明**: 服务器响应客户端的ping消息，用于保持连接活跃

**消息结构**:
```json
{
  "type": "pong",
  "message": "连接正常"
}
```

---

### 2. 批量上传进度消息

**类型**: `batch_upload_progress`

**说明**: 批量上传过程中，每个文件的上传进度更新

**消息结构**:
```json
{
  "type": "batch_upload_progress",
  "file_index": 0,
  "filename": "video1.mp4",
  "status": "uploading",
  "progress": 50,
  "completed": 1,
  "total": 5,
  "video_id": "abc123",
  "error": "错误信息（仅在失败时）"
}
```

**字段说明**:
- `file_index` (integer): 文件在批量上传中的索引（从0开始）
- `filename` (string): 文件名
- `status` (string): 上传状态
  - `uploading`: 正在上传
  - `completed`: 上传完成
  - `failed`: 上传失败
- `progress` (integer): 上传进度百分比（0-100）
- `completed` (integer): 已完成的文件数量
- `total` (integer): 总文件数量
- `video_id` (string, optional): 上传成功后的视频ID
- `error` (string, optional): 失败时的错误信息

**示例场景**:
```json
// 开始上传第一个文件
{
  "type": "batch_upload_progress",
  "file_index": 0,
  "filename": "video1.mp4",
  "status": "uploading",
  "progress": 0,
  "completed": 0,
  "total": 3
}

// 第一个文件上传完成
{
  "type": "batch_upload_progress",
  "file_index": 0,
  "filename": "video1.mp4",
  "status": "completed",
  "progress": 100,
  "video_id": "abc123",
  "completed": 1,
  "total": 3
}

// 第二个文件上传失败
{
  "type": "batch_upload_progress",
  "file_index": 1,
  "filename": "video2.mp4",
  "status": "failed",
  "error": "文件大小超过限制 5GB",
  "completed": 2,
  "total": 3
}
```

---

### 3. 批量上传完成消息

**类型**: `batch_upload_complete`

**说明**: 所有文件上传完成后的汇总消息

**消息结构**:
```json
{
  "type": "batch_upload_complete",
  "total": 5,
  "success_count": 4,
  "failed_count": 1
}
```

**字段说明**:
- `total` (integer): 总文件数量
- `success_count` (integer): 成功上传的文件数量
- `failed_count` (integer): 失败的文件数量

---

### 4. 下载开始消息

**类型**: `download_start`

**说明**: 开始从URL下载视频

**消息结构**:
```json
{
  "type": "download_start",
  "message": "开始下载视频...",
  "url": "https://example.com/video.mp4"
}
```

**字段说明**:
- `url` (string): 视频URL

---

### 5. 下载进度消息

**类型**: `download_progress`

**说明**: 视频下载过程中的进度更新

**消息结构**:
```json
{
  "type": "download_progress",
  "progress": 45,
  "downloaded_bytes": 45678900,
  "total_bytes": 102400000,
  "speed": 1024000,
  "eta": 55
}
```

**字段说明**:
- `progress` (integer): 下载进度百分比（0-100）
- `downloaded_bytes` (integer): 已下载字节数
- `total_bytes` (integer): 总字节数
- `speed` (integer): 下载速度（字节/秒）
- `eta` (integer): 预计剩余时间（秒）

---

### 6. 下载完成消息

**类型**: `download_complete`

**说明**: 视频下载完成

**消息结构**:
```json
{
  "type": "download_complete",
  "message": "视频下载完成，正在处理..."
}
```

---

### 7. 格式转换消息

**类型**: `converting`

**说明**: 正在转换视频格式

**消息结构**:
```json
{
  "type": "converting",
  "message": "正在转换视频格式..."
}
```

---

### 8. 元数据提取消息

**类型**: `extracting_metadata`

**说明**: 正在提取视频元数据

**消息结构**:
```json
{
  "type": "extracting_metadata",
  "message": "正在提取视频元数据..."
}
```

---

### 9. 导入完成消息

**类型**: `import_complete`

**说明**: 视频导入完成

**消息结构**:
```json
{
  "type": "import_complete",
  "message": "视频导入完成",
  "video_id": "abc123"
}
```

**字段说明**:
- `video_id` (string): 导入后的视频ID

---

### 10. 任务进度消息

**类型**: `task_progress`

**说明**: 水印去除任务的处理进度

**消息结构**:
```json
{
  "type": "task_progress",
  "task_id": "task_abc123",
  "video_id": "video_xyz789",
  "status": "processing",
  "progress": 50,
  "message": "正在处理视频..."
}
```

**字段说明**:
- `task_id` (string): 任务ID
- `video_id` (string): 视频ID
- `status` (string): 任务状态（`processing`）
- `progress` (integer): 处理进度百分比（0-100）
- `message` (string): 当前处理阶段的描述

**进度阶段**:
- 0%: 开始处理视频
- 30%: 分析水印区域
- 80%: 正在生成输出视频
- 100%: 处理完成

---

### 11. 任务完成消息

**类型**: `task_completed`

**说明**: 水印去除任务成功完成

**消息结构**:
```json
{
  "type": "task_completed",
  "task_id": "task_abc123",
  "video_id": "video_xyz789",
  "status": "completed",
  "progress": 100,
  "message": "处理完成",
  "result": {
    "output_video_id": "output_def456",
    "output_path": "/path/to/output.mp4",
    "processing_mode": "crop_reconstruct",
    "processing_duration": 45.6,
    "parameters": {
      "crop_x": 0,
      "crop_y": 0,
      "crop_width": 1920,
      "crop_height": 1080
    }
  }
}
```

**字段说明**:
- `task_id` (string): 任务ID
- `video_id` (string): 原视频ID
- `status` (string): 任务状态（`completed`）
- `progress` (integer): 100
- `message` (string): 完成消息
- `result` (object): 处理结果
  - `output_video_id` (string): 输出视频ID
  - `output_path` (string): 输出视频路径
  - `processing_mode` (string): 处理模式
  - `processing_duration` (float): 处理耗时（秒）
  - `parameters` (object): 处理参数

---

### 12. 任务失败消息

**类型**: `task_failed`

**说明**: 水印去除任务失败

**消息结构**:
```json
{
  "type": "task_failed",
  "task_id": "task_abc123",
  "video_id": "video_xyz789",
  "status": "failed",
  "message": "处理失败: FFmpeg执行错误",
  "error": "FFmpeg执行错误: 无法打开输入文件"
}
```

**字段说明**:
- `task_id` (string): 任务ID
- `video_id` (string): 视频ID
- `status` (string): 任务状态（`failed`）
- `message` (string): 失败消息
- `error` (string): 详细错误信息

---

### 13. 批量处理完成消息

**类型**: `batch_completed`

**说明**: 批量水印去除任务全部完成

**消息结构**:
```json
{
  "type": "batch_completed",
  "total": 5,
  "completed": 4,
  "failed": 1,
  "message": "批量处理完成: 4个成功, 1个失败"
}
```

**字段说明**:
- `total` (integer): 总任务数
- `completed` (integer): 成功完成的任务数
- `failed` (integer): 失败的任务数
- `message` (string): 汇总消息

---

## 使用场景

### 场景1: 批量上传视频

1. 客户端建立WebSocket连接: `ws://localhost:8000/ws/upload_client_123`
2. 客户端发起批量上传请求: `POST /api/videos/batch-upload?client_id=upload_client_123`
3. 服务器通过WebSocket推送进度:
   - 多个 `batch_upload_progress` 消息（每个文件的进度）
   - 最后一个 `batch_upload_complete` 消息

### 场景2: URL下载视频

1. 客户端建立WebSocket连接: `ws://localhost:8000/ws/download_client_456`
2. 客户端发起下载请求: `POST /api/videos/download` with `client_id=download_client_456`
3. 服务器通过WebSocket推送进度:
   - `download_start`: 开始下载
   - 多个 `download_progress`: 下载进度
   - `download_complete`: 下载完成
   - `extracting_metadata`: 提取元数据
   - `import_complete`: 导入完成

### 场景3: 单个视频水印去除

1. 客户端建立WebSocket连接: `ws://localhost:8000/ws/removal_client_789`
2. 客户端发起去除请求: `POST /api/videos/{video_id}/remove` with `client_id=removal_client_789`
3. 服务器通过WebSocket推送进度:
   - `task_progress` (0%): 开始处理
   - `task_progress` (30%): 分析水印区域
   - `task_progress` (80%): 生成输出视频
   - `task_completed` (100%): 处理完成

### 场景4: 批量水印去除

1. 客户端建立WebSocket连接: `ws://localhost:8000/ws/batch_removal_client_101`
2. 客户端发起批量去除请求: `POST /api/batch/remove` with `client_id=batch_removal_client_101`
3. 服务器通过WebSocket推送进度:
   - 多个 `task_progress` 消息（每个视频的进度）
   - 多个 `task_completed` 或 `task_failed` 消息（每个视频的结果）
   - 最后一个 `batch_completed` 消息

---

## 错误处理

### 连接错误

如果WebSocket连接失败，客户端应该实现重连机制：

```javascript
let ws;
let reconnectInterval = 1000; // 1秒
let maxReconnectInterval = 30000; // 最大30秒

function connect() {
  ws = new WebSocket('ws://localhost:8000/ws/my_client_id');
  
  ws.onopen = () => {
    console.log('WebSocket连接成功');
    reconnectInterval = 1000; // 重置重连间隔
  };
  
  ws.onclose = () => {
    console.log('WebSocket连接关闭，尝试重连...');
    setTimeout(() => {
      reconnectInterval = Math.min(reconnectInterval * 2, maxReconnectInterval);
      connect();
    }, reconnectInterval);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket错误:', error);
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleMessage(message);
  };
}

connect();
```

### 消息处理错误

客户端应该验证收到的消息格式：

```javascript
function handleMessage(message) {
  if (!message.type) {
    console.error('无效的消息格式:', message);
    return;
  }
  
  switch (message.type) {
    case 'batch_upload_progress':
      handleUploadProgress(message);
      break;
    case 'download_progress':
      handleDownloadProgress(message);
      break;
    case 'task_progress':
      handleTaskProgress(message);
      break;
    case 'task_completed':
      handleTaskCompleted(message);
      break;
    case 'task_failed':
      handleTaskFailed(message);
      break;
    default:
      console.log('未知消息类型:', message.type);
  }
}
```

---

## 最佳实践

1. **使用唯一的client_id**: 每个客户端会话应该使用唯一的client_id，避免消息混淆
2. **实现心跳机制**: 定期发送ping消息保持连接活跃
3. **实现重连机制**: 网络断开时自动重连
4. **消息队列**: 在连接断开期间缓存消息，重连后重新发送
5. **错误处理**: 妥善处理各种错误情况
6. **超时处理**: 设置合理的超时时间，避免长时间等待

---

## 安全考虑

1. **认证**: 在生产环境中，应该在WebSocket连接时进行身份验证
2. **授权**: 验证client_id是否属于当前用户
3. **限流**: 限制每个客户端的连接数和消息频率
4. **输入验证**: 验证所有客户端发送的消息

---

## 性能优化

1. **消息批处理**: 对于高频率的进度更新，可以批量发送
2. **消息压缩**: 对于大量数据，可以使用压缩
3. **连接池**: 服务器端使用连接池管理WebSocket连接
4. **负载均衡**: 使用Redis等中间件实现跨服务器的WebSocket消息分发
