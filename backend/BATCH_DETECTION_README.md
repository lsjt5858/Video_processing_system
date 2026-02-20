# 批量检测功能文档

## 概述

批量检测功能允许用户一次性对多个视频执行帧提取和水印标记操作，提高处理效率。

## 功能特性

### 1. 批量帧提取
- 支持一次提取多个视频的预览帧
- 可自定义每个视频提取的帧数（默认10帧）
- 自动生成缩略图并保存到thumbnails目录
- 返回每个视频的帧信息（帧索引、时间戳、缩略图URL）

### 2. 批量水印标记
- 支持一次标记多个视频的水印区域
- 每个视频可以标记多个水印区域
- 自动验证边界框坐标的有效性
- 自动保存到数据库

### 3. 错误处理
- 单个视频处理失败不影响其他视频
- 返回详细的成功/失败统计
- 每个视频都有独立的状态和错误信息

## API端点

### 1. 批量检测端点

**端点**: `POST /api/batch/detect`

**描述**: 批量提取多个视频的预览帧

**请求体**:
```json
{
  "video_ids": ["video1", "video2", "video3"],
  "num_frames": 10
}
```

**参数说明**:
- `video_ids` (必需): 视频ID列表
- `num_frames` (可选): 每个视频要提取的帧数，默认10

**响应**:
```json
{
  "success": true,
  "data": {
    "total_count": 3,
    "success_count": 3,
    "failed_count": 0,
    "results": [
      {
        "video_id": "video1",
        "status": "success",
        "frames": [
          {
            "frame_index": 0,
            "timestamp": 0.0,
            "thumbnail_url": "/thumbnails/video1_frame_0.jpg"
          },
          {
            "frame_index": 100,
            "timestamp": 3.33,
            "thumbnail_url": "/thumbnails/video1_frame_100.jpg"
          }
        ],
        "error": null
      },
      {
        "video_id": "video2",
        "status": "success",
        "frames": [...],
        "error": null
      }
    ]
  }
}
```

**错误响应**:
```json
{
  "success": true,
  "data": {
    "total_count": 2,
    "success_count": 1,
    "failed_count": 1,
    "results": [
      {
        "video_id": "video1",
        "status": "success",
        "frames": [...],
        "error": null
      },
      {
        "video_id": "video2",
        "status": "failed",
        "frames": null,
        "error": "无法打开视频文件: /path/to/video2.mp4"
      }
    ]
  }
}
```

### 2. 批量标记端点

**端点**: `POST /api/batch/mark`

**描述**: 批量标记多个视频的水印区域

**请求体**:
```json
{
  "watermark_data": [
    {
      "video_id": "video1",
      "bounding_boxes": [
        {
          "x": 10,
          "y": 10,
          "width": 100,
          "height": 50,
          "start_time": 0.0,
          "end_time": 10.0,
          "watermark_type": "corner"
        },
        {
          "x": 1800,
          "y": 10,
          "width": 100,
          "height": 50,
          "start_time": 0.0,
          "end_time": 10.0,
          "watermark_type": "corner"
        }
      ]
    },
    {
      "video_id": "video2",
      "bounding_boxes": [
        {
          "x": 50,
          "y": 50,
          "width": 200,
          "height": 100,
          "start_time": 0.0,
          "end_time": 20.0,
          "watermark_type": "logo"
        }
      ]
    }
  ]
}
```

**参数说明**:
- `watermark_data` (必需): 水印数据列表
  - `video_id` (必需): 视频ID
  - `bounding_boxes` (必需): 边界框列表
    - `x` (必需): 左上角x坐标
    - `y` (必需): 左上角y坐标
    - `width` (必需): 宽度
    - `height` (必需): 高度
    - `start_time` (可选): 开始时间（秒），默认0.0
    - `end_time` (可选): 结束时间（秒），默认视频总时长
    - `watermark_type` (可选): 水印类型，默认"manual"

**响应**:
```json
{
  "success": true,
  "data": {
    "total_count": 2,
    "success_count": 2,
    "failed_count": 0,
    "results": [
      {
        "video_id": "video1",
        "status": "success",
        "regions": [
          {
            "region_id": "reg_abc123",
            "video_id": "video1",
            "bbox": {
              "x": 10,
              "y": 10,
              "width": 100,
              "height": 50
            },
            "start_time": 0.0,
            "end_time": 10.0,
            "confidence": 1.0,
            "watermark_type": "corner",
            "detection_method": "manual"
          },
          {
            "region_id": "reg_def456",
            "video_id": "video1",
            "bbox": {
              "x": 1800,
              "y": 10,
              "width": 100,
              "height": 50
            },
            "start_time": 0.0,
            "end_time": 10.0,
            "confidence": 1.0,
            "watermark_type": "corner",
            "detection_method": "manual"
          }
        ],
        "error": null
      },
      {
        "video_id": "video2",
        "status": "success",
        "regions": [...],
        "error": null
      }
    ]
  }
}
```

## 使用示例

### 示例1: 批量提取预览帧

```bash
curl -X POST http://localhost:8000/api/batch/detect \
  -H "Content-Type: application/json" \
  -d '{
    "video_ids": ["video1", "video2", "video3"],
    "num_frames": 10
  }'
```

### 示例2: 批量标记水印

```bash
curl -X POST http://localhost:8000/api/batch/mark \
  -H "Content-Type: application/json" \
  -d '{
    "watermark_data": [
      {
        "video_id": "video1",
        "bounding_boxes": [
          {
            "x": 10,
            "y": 10,
            "width": 100,
            "height": 50,
            "start_time": 0.0,
            "end_time": 10.0,
            "watermark_type": "corner"
          }
        ]
      }
    ]
  }'
```

### 示例3: Python客户端

```python
import requests

# 批量检测
response = requests.post(
    "http://localhost:8000/api/batch/detect",
    json={
        "video_ids": ["video1", "video2"],
        "num_frames": 10
    }
)
result = response.json()
print(f"成功: {result['data']['success_count']}")
print(f"失败: {result['data']['failed_count']}")

# 批量标记
response = requests.post(
    "http://localhost:8000/api/batch/mark",
    json={
        "watermark_data": [
            {
                "video_id": "video1",
                "bounding_boxes": [
                    {
                        "x": 10,
                        "y": 10,
                        "width": 100,
                        "height": 50,
                        "watermark_type": "corner"
                    }
                ]
            }
        ]
    }
)
result = response.json()
print(f"标记成功: {result['data']['success_count']}")
```

## 工作流程

### 典型使用流程

1. **上传视频**
   ```bash
   # 批量上传多个视频
   POST /api/videos/batch-upload
   ```

2. **批量提取预览帧**
   ```bash
   # 获取所有视频的预览帧
   POST /api/batch/detect
   ```

3. **用户标记水印**
   - 前端显示所有视频的预览帧
   - 用户在每个视频的预览帧上框选水印区域

4. **批量保存标记**
   ```bash
   # 保存所有视频的水印标记
   POST /api/batch/mark
   ```

5. **批量去除水印**
   ```bash
   # 执行批量水印去除（待实现）
   POST /api/batch/remove
   ```

## 实现细节

### 核心函数

#### 1. batch_extract_frames
```python
async def batch_extract_frames(
    video_paths: List[Tuple[str, str]],
    num_frames: int = 10
) -> dict
```

**功能**: 批量提取多个视频的预览帧

**参数**:
- `video_paths`: 视频路径列表，每个元素为 (video_id, video_path)
- `num_frames`: 每个视频要提取的帧数

**返回**: 包含所有视频提取结果的字典

#### 2. batch_mark_watermarks
```python
async def batch_mark_watermarks(
    db,
    watermark_data: List[dict]
) -> dict
```

**功能**: 批量标记多个视频的水印区域

**参数**:
- `db`: 数据库会话
- `watermark_data`: 水印数据列表

**返回**: 包含所有视频标记结果的字典

### 错误处理

批量操作采用"尽力而为"策略：
- 单个视频处理失败不会中断整个批量操作
- 每个视频都有独立的状态（success/failed）
- 失败的视频会记录详细的错误信息
- 返回统计信息（总数、成功数、失败数）

### 性能考虑

- 帧提取是CPU密集型操作，建议控制并发数量
- 缩略图自动调整大小（最大宽度800px）以减小存储空间
- 数据库操作使用异步方式，提高并发性能

## 测试

运行测试：
```bash
cd backend
python test_batch_detection.py
python test_batch_detection_api.py
```

## 注意事项

1. **视频ID验证**: 确保提供的video_id在数据库中存在
2. **边界框验证**: 边界框坐标必须在视频尺寸范围内
3. **时间范围验证**: end_time必须大于start_time
4. **水印类型**: 支持的类型包括 corner, rolling, logo, subtitle, manual
5. **并发控制**: 建议根据服务器性能控制批量操作的视频数量

## 未来改进

- [ ] 添加并发控制（限制同时处理的视频数量）
- [ ] 添加进度推送（通过WebSocket实时推送处理进度）
- [ ] 添加缓存机制（缓存已提取的预览帧）
- [ ] 支持自定义帧提取策略（关键帧、均匀分布、场景切换等）
- [ ] 添加批量删除水印标记功能
