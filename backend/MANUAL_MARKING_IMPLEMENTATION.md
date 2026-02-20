# 手动水印标记功能实现文档

## 概述

本文档描述了任务 4.2 "实现手动标记功能" 的实现细节。该功能允许用户手动标记视频中的水印区域，并将标记信息保存到数据库。

## 实现的功能

### 1. 视频帧预览接口

已在 `watermark_detection.py` 中实现 `extract_frames_for_preview()` 函数：
- 从视频中提取指定数量的关键帧
- 生成缩略图用于前端预览
- 返回帧信息列表（帧索引、时间戳、缩略图URL）

### 2. 边界框坐标验证

实现了 `validate_bounding_box()` 函数：
- 验证坐标是否为负数
- 验证宽度和高度是否为正数
- 验证边界框是否超出视频范围
- 返回布尔值表示验证结果

### 3. 保存水印区域信息到数据库

实现了 `save_manual_watermark_region()` 函数：
- 接收边界框坐标和时间范围
- 验证参数有效性
- 使用现有的 CRUD 操作保存到数据库
- 自动生成唯一的区域ID
- 设置置信度为 1.0（手动标记）
- 设置检测方法为 "manual"

### 4. 支持多个水印区域标记

实现了 `mark_watermark_regions()` 函数：
- 批量处理多个边界框
- 自动获取视频尺寸信息
- 验证每个边界框的有效性
- 批量保存到数据库
- 返回所有保存的水印区域列表

## 核心函数

### validate_bounding_box()

```python
async def validate_bounding_box(
    bbox: BoundingBox,
    video_width: int,
    video_height: int
) -> bool
```

**功能**: 验证边界框坐标是否有效

**参数**:
- `bbox`: BoundingBox对象，包含 x, y, width, height
- `video_width`: 视频宽度
- `video_height`: 视频高度

**返回**: bool - 边界框是否有效

**验证规则**:
1. x 和 y 坐标不能为负数
2. width 和 height 必须大于 0
3. x + width 不能超过视频宽度
4. y + height 不能超过视频高度

### save_manual_watermark_region()

```python
async def save_manual_watermark_region(
    db,
    video_id: str,
    bbox: BoundingBox,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
    watermark_type: str = "manual",
    video_duration: Optional[float] = None
) -> WatermarkRegion
```

**功能**: 保存单个手动标记的水印区域到数据库

**参数**:
- `db`: 数据库会话
- `video_id`: 视频ID
- `bbox`: 边界框对象
- `start_time`: 开始时间（秒），默认 0.0
- `end_time`: 结束时间（秒），如果为 None 则使用视频总时长
- `watermark_type`: 水印类型，默认 "manual"
- `video_duration`: 视频总时长（秒）

**返回**: WatermarkRegion - 保存的水印区域对象

**异常**:
- `ValueError`: 参数验证失败

### mark_watermark_regions()

```python
async def mark_watermark_regions(
    db,
    video_id: str,
    video_path: str,
    bounding_boxes: List[dict]
) -> List[WatermarkRegion]
```

**功能**: 批量标记水印区域

**参数**:
- `db`: 数据库会话
- `video_id`: 视频ID
- `video_path`: 视频文件路径
- `bounding_boxes`: 边界框列表，每个元素包含:
  - `x`: 左上角x坐标
  - `y`: 左上角y坐标
  - `width`: 宽度
  - `height`: 高度
  - `start_time`: 开始时间（可选，默认 0.0）
  - `end_time`: 结束时间（可选，默认视频总时长）
  - `watermark_type`: 水印类型（可选，默认 "manual"）

**返回**: List[WatermarkRegion] - 保存的水印区域列表

**异常**:
- `ValueError`: 边界框验证失败
- `FrameExtractionError`: 无法获取视频信息

## 数据流程

1. **前端发送标记请求**
   - 用户在视频帧上拖拽绘制矩形框
   - 前端收集边界框坐标 (x, y, width, height)
   - 发送到后端 API

2. **后端处理**
   - 接收边界框坐标列表
   - 打开视频文件获取尺寸信息
   - 验证每个边界框的有效性
   - 调用 CRUD 操作保存到数据库

3. **数据库存储**
   - 使用 `crud.create_watermark_region()` 保存
   - 自动生成唯一的 region_id
   - 设置 detection_method = "manual"
   - 设置 confidence = 1.0

4. **返回结果**
   - 返回保存的水印区域列表
   - 包含完整的区域信息（ID、坐标、时间范围等）

## 测试

### 单元测试 (test_manual_marking.py)

测试覆盖：
- ✅ 有效边界框验证
- ✅ 负坐标边界框（Pydantic 模型层验证）
- ✅ 零宽度边界框（Pydantic 模型层验证）
- ✅ 超出视频宽度的边界框
- ✅ 超出视频高度的边界框
- ✅ 边界情况：边界框刚好在视频边缘
- ✅ 缺少必需参数时抛出异常
- ✅ 无效开始时间
- ✅ 无效时间范围

### 集成测试 (test_manual_marking_integration.py)

测试覆盖：
- ✅ 使用真实视频提取预览帧
- ✅ 使用真实视频标记多个水印区域
- ✅ 标记无效边界框时正确抛出异常

**注意**: 集成测试需要真实的视频文件。如果没有测试视频，测试会自动跳过。

## 与现有代码的集成

### 使用现有的 CRUD 操作

本实现完全依赖于已有的 `crud.py` 中的函数：
- `crud.create_watermark_region()`: 创建水印区域记录
- `crud.get_watermark_regions_by_video()`: 获取视频的所有水印区域

### 使用现有的数据模型

使用 `models.py` 中定义的数据模型：
- `BoundingBox`: 边界框模型（包含 Pydantic 验证）
- `WatermarkRegion`: 水印区域模型

### 使用现有的数据库表

使用 `database.py` 中定义的 `watermark_regions` 表：
- 所有字段都已存在
- 支持级联删除（删除视频时自动删除水印区域）

## API 端点建议

虽然本任务只实现了核心功能，但建议在 `main.py` 中添加以下 API 端点：

```python
@app.get("/api/videos/{video_id}/frames")
async def get_video_frames(video_id: str, num_frames: int = 10):
    """获取视频帧用于预览"""
    # 调用 extract_frames_for_preview()
    pass

@app.post("/api/videos/{video_id}/watermarks")
async def mark_watermarks(video_id: str, bounding_boxes: List[dict]):
    """标记水印区域"""
    # 调用 mark_watermark_regions()
    pass

@app.get("/api/videos/{video_id}/watermarks")
async def get_watermarks(video_id: str):
    """获取视频的所有水印区域"""
    # 调用 crud.get_watermark_regions_by_video()
    pass
```

## 验收标准完成情况

根据任务 4.2 的要求：

- ✅ **提供视频帧预览接口**: `extract_frames_for_preview()` 函数
- ✅ **接收前端传来的矩形框坐标**: `mark_watermark_regions()` 接收边界框列表
- ✅ **保存水印区域信息到数据库**: 使用 `crud.create_watermark_region()` 保存
- ✅ **支持多个水印区域标记**: `mark_watermark_regions()` 支持批量标记

## 下一步

1. 在 `main.py` 中添加 API 端点
2. 实现前端界面（任务 8.3）
3. 添加更多的错误处理和日志记录
4. 考虑添加水印区域的更新和删除功能

## 总结

任务 4.2 已成功实现，所有核心功能都已完成并通过测试。实现遵循了现有的代码结构和设计模式，与 CRUD 操作和数据模型无缝集成。
