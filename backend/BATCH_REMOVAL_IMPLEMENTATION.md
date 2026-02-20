# 批量水印去除功能实现文档

## 概述

本文档描述了任务 5.3 的实现：批量水印去除功能。该功能允许用户同时处理多个视频的水印去除任务，支持并发处理（最多3个视频并行），并通过WebSocket实时推送处理进度。

## 实现的功能

### 1. 批量去除API端点

#### POST /api/batch/remove

批量执行水印去除任务。

**请求体：**
```json
{
  "removal_tasks": [
    {
      "video_id": "vid_123",
      "regions": [
        {
          "region_id": "reg_001",
          "bbox": {
            "x": 1700,
            "y": 50,
            "width": 200,
            "height": 100
          },
          "start_time": 0.0,
          "end_time": 120.0,
          "confidence": 0.95,
          "watermark_type": "corner",
          "detection_method": "manual"
        }
      ]
    }
  ],
  "user_id": "test_user",
  "client_id": "optional_websocket_client_id"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "job_id": "batch_abc123",
    "task_ids": ["task_001", "task_002", "task_003"],
    "total_count": 3,
    "status": "processing",
    "message": "批量处理已启动，共 3 个视频"
  }
}
```

**功能特性：**
- 为每个视频创建独立的处理任务
- 支持为不同视频应用相同或不同的裁剪参数
- 异步执行批量处理，立即返回job_id
- 可选的WebSocket进度推送（通过client_id）
- 自动验证视频是否存在
- 错误隔离：单个视频失败不影响其他视频

#### GET /api/batch/{job_id}

查询批量任务的状态。

**响应：**
```json
{
  "success": true,
  "data": {
    "job_id": "batch_abc123",
    "status": "processing",
    "total_count": 3,
    "completed_count": 1,
    "failed_count": 0,
    "processing_count": 1,
    "pending_count": 1,
    "tasks": [
      {
        "task_id": "task_001",
        "video_id": "vid_123",
        "status": "completed",
        "created_at": "2024-01-15T10:30:00Z",
        "started_at": "2024-01-15T10:30:05Z",
        "completed_at": "2024-01-15T10:30:15Z",
        "error_message": null,
        "result": {
          "output_video_id": "output_001",
          "output_path": "/outputs/output_001.mp4",
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
      }
    ]
  }
}
```

**状态说明：**
- `completed`: 所有任务都成功完成
- `failed`: 所有任务都失败
- `completed_with_errors`: 部分任务成功，部分失败
- `processing`: 仍有任务在处理中

### 2. 后端实现

#### 核心组件

1. **TaskProcessor.process_batch_removal()**
   - 位置：`backend/app/task_processor.py`
   - 功能：并发处理多个水印去除任务
   - 并发控制：使用asyncio.Semaphore限制最多3个并发任务
   - 错误处理：单个任务失败不影响其他任务
   - WebSocket支持：可选的实时进度推送

2. **批量去除API端点**
   - 位置：`backend/app/main.py`
   - 功能：接收批量去除请求，创建任务记录，启动异步处理
   - 验证：检查视频是否存在
   - 任务管理：为每个视频创建独立的processing_task记录

3. **批量状态查询API端点**
   - 位置：`backend/app/main.py`
   - 功能：查询批量任务的整体状态和每个子任务的详细信息
   - 统计：自动计算completed、failed、processing、pending任务数

#### 数据流程

```
1. 客户端提交批量去除请求
   ↓
2. API验证视频存在性
   ↓
3. 为每个视频创建processing_task记录
   ↓
4. 生成job_id并返回给客户端
   ↓
5. 异步启动批量处理（不阻塞响应）
   ↓
6. TaskProcessor使用Semaphore控制并发（最多3个）
   ↓
7. 每个任务调用removal_engine.crop_reconstruct()
   ↓
8. 更新任务状态（processing → completed/failed）
   ↓
9. 通过WebSocket推送进度（如果提供了client_id）
   ↓
10. 客户端可随时查询批量任务状态
```

### 3. WebSocket进度推送

如果在请求中提供了`client_id`，系统会通过WebSocket推送以下消息：

**任务开始：**
```json
{
  "type": "task_progress",
  "task_id": "task_001",
  "video_id": "vid_123",
  "status": "processing",
  "progress": 0,
  "message": "开始处理视频..."
}
```

**处理进度：**
```json
{
  "type": "task_progress",
  "task_id": "task_001",
  "video_id": "vid_123",
  "status": "processing",
  "progress": 30,
  "message": "分析水印区域..."
}
```

**任务完成：**
```json
{
  "type": "task_completed",
  "task_id": "task_001",
  "video_id": "vid_123",
  "status": "completed",
  "progress": 100,
  "message": "处理完成",
  "result": {
    "output_video_id": "output_001",
    "output_path": "/outputs/output_001.mp4"
  }
}
```

**批量完成：**
```json
{
  "type": "batch_completed",
  "total": 3,
  "completed": 2,
  "failed": 1,
  "message": "批量处理完成: 2个成功, 1个失败"
}
```

## 测试

### 测试文件

- `backend/test_batch_removal_api.py` - 批量去除API的完整测试套件

### 测试覆盖

#### 1. 批量去除API测试（TestBatchRemovalAPI）

- ✅ `test_batch_remove_success` - 测试批量去除成功
- ✅ `test_batch_remove_with_websocket` - 测试带WebSocket的批量去除
- ✅ `test_batch_remove_video_not_found` - 测试视频不存在的情况
- ✅ `test_batch_remove_empty_tasks` - 测试空任务列表
- ✅ `test_batch_remove_same_video_different_regions` - 测试同一视频应用不同裁剪参数
- ✅ `test_batch_remove_max_concurrent` - 测试最多3个视频并行处理

#### 2. 批量状态查询API测试（TestBatchStatusAPI）

- ✅ `test_get_batch_status_success` - 测试获取批量任务状态成功
- ✅ `test_get_batch_status_all_completed` - 测试所有任务都完成的情况
- ✅ `test_get_batch_status_all_failed` - 测试所有任务都失败的情况
- ✅ `test_get_batch_status_processing` - 测试正在处理中的批量任务
- ✅ `test_get_batch_status_not_found` - 测试批量任务不存在
- ✅ `test_get_batch_status_task_details` - 测试任务详情包含完整信息

#### 3. 集成测试（TestBatchRemovalIntegration）

- ✅ `test_full_batch_removal_workflow` - 测试完整的批量去除工作流

### 运行测试

```bash
# 运行批量去除API测试
cd backend
python -m pytest test_batch_removal_api.py -v

# 运行所有测试
python -m pytest test_batch_removal_api.py test_task_processor.py -v
```

### 测试结果

```
test_batch_removal_api.py::TestBatchRemovalAPI::test_batch_remove_success PASSED
test_batch_removal_api.py::TestBatchRemovalAPI::test_batch_remove_with_websocket PASSED
test_batch_removal_api.py::TestBatchRemovalAPI::test_batch_remove_video_not_found PASSED
test_batch_removal_api.py::TestBatchRemovalAPI::test_batch_remove_empty_tasks PASSED
test_batch_removal_api.py::TestBatchRemovalAPI::test_batch_remove_same_video_different_regions PASSED
test_batch_removal_api.py::TestBatchRemovalAPI::test_batch_remove_max_concurrent PASSED
test_batch_removal_api.py::TestBatchStatusAPI::test_get_batch_status_success PASSED
test_batch_removal_api.py::TestBatchStatusAPI::test_get_batch_status_all_completed PASSED
test_batch_removal_api.py::TestBatchStatusAPI::test_get_batch_status_all_failed PASSED
test_batch_removal_api.py::TestBatchStatusAPI::test_get_batch_status_processing PASSED
test_batch_removal_api.py::TestBatchStatusAPI::test_get_batch_status_not_found PASSED
test_batch_removal_api.py::TestBatchStatusAPI::test_get_batch_status_task_details PASSED
test_batch_removal_api.py::TestBatchRemovalIntegration::test_full_batch_removal_workflow PASSED

===================== 13 passed in 3.06s ======================
```

## 使用示例

### 1. 提交批量去除任务

```python
import requests

# 准备批量任务数据
removal_tasks = [
    {
        "video_id": "vid_001",
        "regions": [
            {
                "region_id": "reg_001",
                "bbox": {"x": 1700, "y": 50, "width": 200, "height": 100},
                "start_time": 0.0,
                "end_time": 120.0,
                "confidence": 0.95,
                "watermark_type": "corner",
                "detection_method": "manual"
            }
        ]
    },
    {
        "video_id": "vid_002",
        "regions": [
            {
                "region_id": "reg_002",
                "bbox": {"x": 50, "y": 50, "width": 150, "height": 80},
                "start_time": 0.0,
                "end_time": 90.0,
                "confidence": 0.90,
                "watermark_type": "logo",
                "detection_method": "manual"
            }
        ]
    }
]

# 提交批量去除请求
response = requests.post(
    "http://localhost:8000/api/batch/remove",
    json={
        "removal_tasks": removal_tasks,
        "user_id": "user_123",
        "client_id": "ws_client_456"  # 可选，用于WebSocket进度推送
    }
)

result = response.json()
job_id = result["data"]["job_id"]
print(f"批量任务已启动，job_id: {job_id}")
```

### 2. 查询批量任务状态

```python
import requests
import time

# 轮询查询任务状态
while True:
    response = requests.get(f"http://localhost:8000/api/batch/{job_id}")
    data = response.json()["data"]
    
    print(f"状态: {data['status']}")
    print(f"完成: {data['completed_count']}/{data['total_count']}")
    print(f"失败: {data['failed_count']}")
    
    if data['status'] in ['completed', 'failed', 'completed_with_errors']:
        print("批量处理完成！")
        
        # 打印每个任务的结果
        for task in data['tasks']:
            print(f"  任务 {task['task_id']}: {task['status']}")
            if task['result']:
                print(f"    输出: {task['result']['output_path']}")
        break
    
    time.sleep(2)  # 每2秒查询一次
```

### 3. 使用WebSocket接收实时进度

```javascript
// 前端JavaScript示例
const ws = new WebSocket('ws://localhost:8000/ws/ws_client_456');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'task_progress':
      console.log(`任务 ${message.task_id}: ${message.progress}% - ${message.message}`);
      break;
    
    case 'task_completed':
      console.log(`任务 ${message.task_id} 完成！`);
      console.log(`输出文件: ${message.result.output_path}`);
      break;
    
    case 'task_failed':
      console.error(`任务 ${message.task_id} 失败: ${message.error}`);
      break;
    
    case 'batch_completed':
      console.log(`批量处理完成: ${message.completed}个成功, ${message.failed}个失败`);
      break;
  }
};

// 提交批量去除请求
fetch('http://localhost:8000/api/batch/remove', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    removal_tasks: [...],
    user_id: 'user_123',
    client_id: 'ws_client_456'
  })
});
```

## 技术细节

### 并发控制

使用`asyncio.Semaphore`实现并发限制：

```python
semaphore = asyncio.Semaphore(self.max_concurrent_tasks)  # 最多3个

async def process_with_semaphore(task_data):
    async with semaphore:
        # 处理任务
        result = await self.process_removal_task(...)
    return result

# 并发处理所有任务
tasks = [process_with_semaphore(task_data) for task_data in batch_tasks]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 错误隔离

每个任务独立处理，使用try-except捕获异常：

```python
try:
    result = await self.process_removal_task(...)
    return {"status": "completed", "result": result}
except Exception as e:
    return {"status": "failed", "error": str(e)}
```

### 数据库事务管理

- 任务创建时立即提交到数据库
- 任务状态更新使用独立的事务
- 避免长时间持有数据库连接

## 性能考虑

1. **并发限制**：最多3个视频并行处理，避免系统过载
2. **异步处理**：批量任务异步执行，API立即返回
3. **WebSocket推送**：实时进度更新，无需轮询
4. **错误隔离**：单个任务失败不影响其他任务
5. **数据库优化**：使用索引加速任务查询

## 已知限制

1. 目前只支持裁剪重构模式（crop_reconstruct）
2. WebSocket连接需要客户端主动建立
3. 批量任务没有总体超时限制
4. 不支持批量任务的取消操作

## 未来改进

1. 支持AI修复填充和局部模糊替换模式
2. 添加批量任务取消功能
3. 实现任务优先级队列
4. 添加批量任务的总体超时控制
5. 支持批量导出功能（ZIP打包）
6. 添加任务重试机制
7. 实现更细粒度的进度报告（如FFmpeg处理进度）

## 总结

任务 5.3 已成功实现，提供了完整的批量水印去除功能：

✅ 批量去除API端点（POST /api/batch/remove）
✅ 批量状态查询API端点（GET /api/batch/{job_id}）
✅ 并发控制（最多3个视频并行）
✅ WebSocket实时进度推送
✅ 错误隔离（单个失败不影响其他）
✅ 支持相同或不同的裁剪参数
✅ 完整的测试覆盖（13个测试用例全部通过）

该实现满足了设计文档中的所有要求，并提供了良好的用户体验和系统稳定性。
