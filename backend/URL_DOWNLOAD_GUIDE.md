# URL视频下载功能使用指南

## 概述

URL视频下载功能允许用户通过提供视频链接来下载视频，支持YouTube、Bilibili等常见视频网站。该功能使用yt-dlp库实现，支持实时进度推送。

## 功能特性

1. **多平台支持**：支持YouTube、Bilibili、Twitter等常见视频网站
2. **实时进度推送**：通过WebSocket实时推送下载进度
3. **自动格式转换**：自动将不支持的格式转换为MP4
4. **元数据提取**：下载完成后自动提取视频元数据
5. **错误处理**：完善的错误处理机制，提供清晰的错误信息

## API端点

### POST /api/videos/download

下载指定URL的视频

**请求体：**

```json
{
  "url": "https://www.youtube.com/watch?v=example",
  "user_id": "user123",
  "client_id": "client_abc"
}
```

**参数说明：**

- `url` (必需): 视频链接
- `user_id` (可选): 用户ID，默认为 "default_user"
- `client_id` (可选): 客户端ID，用于WebSocket进度推送

**成功响应 (200)：**

```json
{
  "success": true,
  "data": {
    "video_id": "uuid-string",
    "url": "https://www.youtube.com/watch?v=example",
    "file_size": 10485760,
    "format": "mp4",
    "resolution": [1920, 1080],
    "duration": 120.5,
    "storage_path": "/path/to/video.mp4",
    "import_time": "2024-01-15T10:30:00"
  }
}
```

**错误响应：**

- `400 Bad Request`: 无效的URL
- `404 Not Found`: 视频不可访问
- `415 Unsupported Media Type`: 不支持的视频格式
- `500 Internal Server Error`: 服务器内部错误

## WebSocket进度推送

如果在请求中提供了`client_id`，系统会通过WebSocket推送下载进度。

### 连接WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client_abc');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### 进度消息类型

1. **下载开始**

```json
{
  "type": "download_start",
  "message": "开始下载视频...",
  "url": "https://www.youtube.com/watch?v=example"
}
```

2. **下载进度**

```json
{
  "type": "download_progress",
  "progress": 50,
  "downloaded_bytes": 5242880,
  "total_bytes": 10485760,
  "speed": 1048576,
  "eta": 5
}
```

3. **下载完成**

```json
{
  "type": "download_complete",
  "message": "视频下载完成，正在处理..."
}
```

4. **格式转换**

```json
{
  "type": "converting",
  "message": "正在转换视频格式..."
}
```

5. **元数据提取**

```json
{
  "type": "extracting_metadata",
  "message": "正在提取视频元数据..."
}
```

6. **导入完成**

```json
{
  "type": "import_complete",
  "message": "视频导入完成",
  "video_id": "uuid-string"
}
```

## 使用示例

### Python示例

```python
import requests

# 下载视频
response = requests.post(
    'http://localhost:8000/api/videos/download',
    json={
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'user_id': 'user123',
        'client_id': 'client_abc'
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"视频ID: {data['data']['video_id']}")
    print(f"文件大小: {data['data']['file_size']} bytes")
else:
    print(f"错误: {response.json()['detail']}")
```

### JavaScript示例

```javascript
// 建立WebSocket连接
const clientId = 'client_' + Date.now();
const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'download_progress':
      console.log(`下载进度: ${data.progress}%`);
      break;
    case 'download_complete':
      console.log('下载完成');
      break;
    case 'import_complete':
      console.log(`视频导入完成，ID: ${data.video_id}`);
      break;
  }
};

// 发起下载请求
fetch('http://localhost:8000/api/videos/download', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    user_id: 'user123',
    client_id: clientId
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('视频下载成功:', data.data);
  } else {
    console.error('下载失败:', data.detail);
  }
});
```

### cURL示例

```bash
# 下载视频
curl -X POST http://localhost:8000/api/videos/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "user_id": "user123"
  }'
```

## 支持的视频网站

yt-dlp支持超过1000个视频网站，包括但不限于：

- YouTube
- Bilibili
- Twitter
- Facebook
- Instagram
- TikTok
- Vimeo
- Dailymotion

完整列表请参考：https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

## 错误处理

### 常见错误及解决方案

1. **InvalidUrlError (400)**
   - 原因：提供的URL格式不正确或不是有效的视频链接
   - 解决：检查URL格式，确保是完整的视频链接

2. **VideoNotAccessibleError (404)**
   - 原因：视频不存在、已删除、私有或地区限制
   - 解决：确认视频可以正常访问，检查是否需要登录或有地区限制

3. **UnsupportedFormatError (415)**
   - 原因：视频格式不支持且无法转换
   - 解决：尝试其他视频源或联系管理员

4. **MetadataExtractionError (500)**
   - 原因：视频文件损坏或格式异常
   - 解决：尝试重新下载或使用其他视频源

## 性能考虑

1. **下载速度**：取决于网络速度和视频大小
2. **格式转换**：如果需要转换格式，会增加额外的处理时间
3. **并发限制**：建议同时下载的视频数量不超过3个
4. **文件大小限制**：下载的视频文件大小不能超过5GB

## 注意事项

1. **版权问题**：请确保您有权下载和使用视频内容
2. **网络要求**：需要稳定的网络连接
3. **存储空间**：确保服务器有足够的存储空间
4. **超时设置**：大文件下载可能需要较长时间，请耐心等待

## 故障排查

### 下载失败

1. 检查URL是否正确
2. 确认视频是否可以正常访问
3. 检查网络连接
4. 查看服务器日志获取详细错误信息

### WebSocket连接失败

1. 确认WebSocket端点正确
2. 检查防火墙设置
3. 确认client_id唯一且有效

### 格式转换失败

1. 确认FFmpeg已正确安装
2. 检查服务器资源（CPU、内存）
3. 查看FFmpeg错误日志

## 技术实现

### 核心组件

1. **yt-dlp**：视频下载库
2. **FFmpeg**：视频格式转换
3. **WebSocket**：实时进度推送
4. **SQLite**：元数据存储

### 处理流程

1. 接收下载请求
2. 验证URL有效性
3. 使用yt-dlp下载视频
4. 通过WebSocket推送进度
5. 格式转换（如需要）
6. 提取视频元数据
7. 保存到数据库
8. 返回结果

## 更新日志

### v1.0.0 (2024-01-15)

- 初始版本
- 支持基本的URL视频下载
- 实现WebSocket进度推送
- 支持自动格式转换
- 完善的错误处理机制
