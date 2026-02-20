# 视频上传后不显示问题修复

## 问题描述

用户在客户端上传视频后，跳转到视频列表页面，但上传的视频不显示。

## 问题原因

在 `backend/app/video_import.py` 文件中，`upload_single_video` 和 `download_video_from_url` 函数在保存视频到数据库后，**没有调用 `commit()` 提交事务**。

虽然数据被添加到数据库会话（session），但由于没有提交，数据实际上从未写入数据库文件。

### 问题代码

```python
db_gen = get_db()
db = await anext(db_gen)
try:
    await create_video(
        db=db,
        # ... 参数
    )
finally:
    await db.close()  # ❌ 直接关闭，没有提交！
```

## 解决方案

在关闭数据库会话之前，添加 `commit()` 调用来提交事务，并在发生错误时回滚。

### 修复后的代码

```python
db_gen = get_db()
db = await anext(db_gen)
try:
    await create_video(
        db=db,
        # ... 参数
    )
    await db.commit()  # ✅ 提交事务
except Exception as e:
    await db.rollback()  # ✅ 发生错误时回滚
    raise
finally:
    await db.close()
```

## 修改的文件

- `backend/app/video_import.py`
  - `upload_single_video()` 函数（第 350-370 行）
  - `download_video_from_url()` 函数（第 775-795 行）

## 验证修复

### 1. 测试上传

```bash
# 创建测试视频
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=30 -pix_fmt yuv420p test.mp4 -y

# 上传视频
curl -X POST http://localhost:8000/api/videos/upload -F "file=@test.mp4"
```

### 2. 检查数据库

```bash
cd backend
sqlite3 video_platform.db "SELECT video_id, format, duration FROM videos;"
```

应该能看到刚上传的视频记录。

### 3. 检查 API

```bash
curl http://localhost:8000/api/videos?page=1&page_size=20
```

应该返回包含上传视频的列表。

### 4. 在客户端测试

1. 打开应用
2. 上传一个视频
3. 跳转到视频列表页面
4. 应该能看到刚上传的视频

## 技术说明

### SQLAlchemy 异步会话管理

在 SQLAlchemy 异步模式下，事务管理需要显式调用：

- `db.add(object)` - 将对象添加到会话
- `await db.flush()` - 将更改发送到数据库（但不提交）
- `await db.commit()` - 提交事务，使更改永久化
- `await db.rollback()` - 回滚事务
- `await db.close()` - 关闭会话

### 为什么 `get_db()` 依赖注入不需要手动提交？

在 FastAPI 路由中使用 `Depends(get_db)` 时，`get_db()` 函数会自动处理提交：

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # ✅ 自动提交
        except Exception:
            await session.rollback()  # ✅ 自动回滚
            raise
        finally:
            await session.close()
```

但在 `video_import.py` 中，我们手动调用 `get_db()` 并使用 `anext()`，所以需要手动管理事务。

## 最佳实践

### 方案 1：手动管理（当前使用）

```python
db_gen = get_db()
db = await anext(db_gen)
try:
    # 数据库操作
    await db.commit()
except Exception:
    await db.rollback()
    raise
finally:
    await db.close()
```

### 方案 2：使用 async with（推荐）

```python
async for db in get_db():
    try:
        # 数据库操作
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    break  # 只需要一次迭代
```

### 方案 3：重构为依赖注入

将 `upload_single_video` 改为接受 `db: AsyncSession` 参数，在路由层使用 `Depends(get_db)`：

```python
# video_import.py
async def upload_single_video(
    file: UploadFile,
    user_id: str,
    db: AsyncSession  # 接受会话参数
) -> VideoImportResult:
    # ... 直接使用 db，不需要手动管理

# main.py
@app.post("/api/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)  # 依赖注入
):
    result = await upload_single_video(file, user_id, db)
    return {"success": True, "data": result}
```

## 相关问题

如果遇到类似的"数据不保存"问题，检查：

1. 是否调用了 `commit()`
2. 是否有异常被静默捕获
3. 数据库文件路径是否正确
4. 是否有多个数据库实例

## 总结

这是一个经典的事务管理问题。在异步数据库操作中，必须显式提交事务才能使更改永久化。修复后，视频上传功能现在可以正常工作了。

✅ 文件保存成功  
✅ 数据库记录保存成功  
✅ 视频列表正常显示
