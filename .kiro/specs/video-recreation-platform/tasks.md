# 实施计划：视频水印去除工具（MVP版本）

## 概述

本实施计划专注于核心功能：视频下载和水印去除。系统采用FastAPI + Python实现，使用FFmpeg进行视频处理，提供简单的Web界面。

核心功能：
1. 视频导入（本地上传 + URL下载 + 批量上传）
2. 水印检测（手动标记为主）
3. 水印去除（裁剪模式）
4. 批量处理（批量检测 + 批量去除）
5. 现代化Web UI（前后端分离）

技术栈：
- 后端：FastAPI + Python 3.10+
- 视频处理：FFmpeg、OpenCV
- 存储：本地文件系统 + SQLite（轻量级数据库）
- 前端：React 18 + Vite + Ant Design + TypeScript
- 实时通信：WebSocket（处理进度推送）

## 任务

- [x] 1. 搭建后端项目基础架构
  - [x] 1.1 创建FastAPI项目结构
    - 创建项目目录结构（backend/app/、uploads/、outputs/）
    - 创建requirements.txt或pyproject.toml
    - 配置.env文件管理环境变量
    
  - [x] 1.2 安装核心依赖
    - 安装FastAPI、uvicorn
    - 安装FFmpeg（系统级）和ffmpeg-python
    - 安装OpenCV（opencv-python）
    - 安装python-multipart（文件上传）
    - 安装yt-dlp（视频下载）
    - 安装websockets（实时通信）
    - 安装aiosqlite（异步SQLite）
    
  - [x] 1.3 创建FastAPI应用入口
    - 创建main.py，初始化FastAPI应用
    - 配置CORS中间件（允许前端跨域）
    - 配置静态文件服务（视频文件访问）
    - 添加健康检查端点
    - 配置WebSocket路由

- [x] 2. 实现数据模型和存储层
  - [x] 2.1 定义核心数据类
    - 创建models.py
    - 定义VideoMetadata（分辨率、时长、格式等）
    - 定义BoundingBox（x, y, width, height）
    - 定义WatermarkRegion（区域信息）
    - 定义ProcessingTask（任务状态）
    - 使用Pydantic进行数据验证
    
  - [x] 2.2 实现SQLite数据库
    - 创建database.py
    - 使用SQLAlchemy定义ORM模型
    - 创建videos、watermark_regions、processing_tasks表
    - 实现数据库初始化和连接管理
    
  - [x] 2.3 实现数据访问层
    - 创建crud.py
    - 实现视频CRUD操作
    - 实现水印区域CRUD操作
    - 实现任务CRUD操作

- [x] 3. 实现视频导入模块
  - [x] 3.1 实现本地视频上传
    - 创建video_import.py
    - 实现单文件上传接口（支持MP4、AVI、MOV、MKV）
    - 实现批量文件上传接口（最多50个文件）
    - 实现文件大小验证（限制5GB）
    - 保存视频到uploads目录
    
  - [x] 3.2 实现视频元数据提取
    - 使用FFprobe提取视频信息
    - 提取分辨率、时长、格式、编码、帧率、码率
    - 保存元数据到数据库
    
  - [x] 3.3 实现URL视频下载
    - 使用yt-dlp下载视频
    - 支持常见视频网站（YouTube、Bilibili等）
    - 实现下载进度WebSocket推送
    - 下载后自动提取元数据
    
  - [x] 3.4 实现批量上传进度管理
    - 创建批量上传任务
    - 并行上传最多5个文件
    - 通过WebSocket推送每个文件的上传进度
    - 单个文件失败不影响其他文件

- [x] 4. 实现水印检测模块
  - [x] 4.1 实现视频帧提取
    - 创建watermark_detection.py
    - 使用OpenCV提取视频关键帧
    - 生成缩略图用于预览
    
  - [x] 4.2 实现手动标记功能
    - 提供视频帧预览接口
    - 接收前端传来的矩形框坐标
    - 保存水印区域信息到数据库
    - 支持多个水印区域标记
    
  - [x] 4.3 实现批量检测功能
    - 创建批量检测任务
    - 对多个视频执行帧提取
    - 返回所有视频的预览帧
    - 支持批量标记水印区域

- [ ] 5. 实现水印去除模块
  - [x] 5.1 实现裁剪重构模式
    - 创建watermark_removal.py
    - 分析水印位置，计算最优裁剪区域
    - 使用FFmpeg执行视频裁剪
    - 保持原始帧率和编码格式
    
  - [x] 5.2 实现异步任务处理
    - 创建task_processor.py
    - 使用asyncio实现异步视频处理
    - 通过WebSocket推送处理进度
    - 处理完成后更新任务状态
    
  - [ ] 5.3 实现批量去除功能
    - 创建批量去除任务
    - 并行处理最多3个视频
    - 为每个视频应用相同或不同的裁剪参数
    - 通过WebSocket推送批量处理进度
    
  - [ ] 5.4 生成处理后的视频
    - 保存处理后视频到outputs目录
    - 生成唯一的输出文件名
    - 返回处理结果和文件路径
    - 提供视频下载接口

- [ ] 6. 实现API端点
  - [ ] 6.1 视频导入API
    - POST /api/videos/upload - 上传单个视频
    - POST /api/videos/batch-upload - 批量上传视频
    - POST /api/videos/download - 通过URL下载视频
    - GET /api/videos - 获取视频列表（支持分页）
    - GET /api/videos/{video_id} - 获取视频详情
    - DELETE /api/videos/{video_id} - 删除视频
    
  - [ ] 6.2 水印检测API
    - GET /api/videos/{video_id}/frames - 获取视频帧
    - POST /api/videos/{video_id}/watermarks - 标记水印区域
    - GET /api/videos/{video_id}/watermarks - 获取水印区域列表
    - PUT /api/videos/{video_id}/watermarks/{region_id} - 更新水印区域
    - DELETE /api/videos/{video_id}/watermarks/{region_id} - 删除水印区域
    - POST /api/batch/detect - 批量检测（返回所有视频的预览帧）
    
  - [ ] 6.3 水印去除API
    - POST /api/videos/{video_id}/remove - 执行单个视频水印去除
    - POST /api/batch/remove - 批量执行水印去除
    - GET /api/tasks/{task_id} - 获取任务状态
    - GET /api/tasks - 获取任务列表
    - GET /api/videos/{video_id}/output - 下载处理后的视频
    
  - [ ] 6.4 WebSocket端点
    - WS /ws/{client_id} - WebSocket连接
    - 推送上传进度
    - 推送下载进度
    - 推送处理进度
    - 推送任务完成通知

- [ ] 7. 搭建前端项目
  - [ ] 7.1 创建React + Vite项目
    - 使用Vite创建React + TypeScript项目
    - 安装Ant Design UI组件库
    - 安装axios（HTTP请求）
    - 安装react-router-dom（路由）
    - 配置代理转发到后端API
    
  - [ ] 7.2 配置项目结构
    - 创建src/pages/（页面组件）
    - 创建src/components/（通用组件）
    - 创建src/services/（API服务）
    - 创建src/hooks/（自定义Hooks）
    - 创建src/types/（TypeScript类型定义）
    - 配置路由

- [ ] 8. 实现前端页面
  - [ ] 8.1 实现视频列表页面
    - 创建VideoList组件
    - 使用Ant Design Table展示视频列表
    - 实现分页、搜索、筛选功能
    - 显示视频缩略图、元数据
    - 提供删除、查看详情按钮
    
  - [ ] 8.2 实现视频上传页面
    - 创建VideoUpload组件
    - 使用Ant Design Upload组件
    - 支持拖拽上传
    - 支持批量选择文件（最多50个）
    - 显示上传进度条
    - 实现URL下载输入框
    
  - [ ] 8.3 实现水印标记页面
    - 创建WatermarkMarker组件
    - 使用HTML5 Canvas绘制视频帧
    - 实现鼠标拖拽绘制矩形框
    - 显示已标记的水印区域列表
    - 支持编辑、删除水印区域
    - 提供批量标记模式（切换不同视频）
    
  - [ ] 8.4 实现水印去除页面
    - 创建WatermarkRemoval组件
    - 显示视频信息和水印区域
    - 提供裁剪参数设置（裁剪模式）
    - 显示裁剪预览
    - 开始处理按钮
    - 实时显示处理进度
    
  - [ ] 8.5 实现批量处理页面
    - 创建BatchProcessing组件
    - 使用Ant Design Table展示批量任务
    - 支持批量选择视频
    - 统一设置处理参数
    - 显示每个视频的处理状态和进度
    - 提供批量下载功能
    
  - [ ] 8.6 实现任务管理页面
    - 创建TaskManager组件
    - 显示所有处理任务列表
    - 显示任务状态（pending、processing、completed、failed）
    - 提供任务取消、重试功能
    - 显示任务详情和错误信息

- [ ] 9. 实现前端核心功能
  - [ ] 9.1 实现API服务层
    - 创建src/services/api.ts
    - 封装所有API调用
    - 实现请求拦截器（添加token等）
    - 实现响应拦截器（错误处理）
    
  - [ ] 9.2 实现WebSocket连接
    - 创建src/services/websocket.ts
    - 实现WebSocket连接管理
    - 实现消息订阅和分发
    - 实现断线重连
    
  - [ ] 9.3 实现状态管理
    - 使用React Context或Zustand
    - 管理视频列表状态
    - 管理任务状态
    - 管理WebSocket连接状态
    
  - [ ] 9.4 实现自定义Hooks
    - useWebSocket - WebSocket连接Hook
    - useVideoUpload - 视频上传Hook
    - useTaskProgress - 任务进度Hook
    - useVideoList - 视频列表Hook
    
  - [ ] 9.5 实现通用组件
    - ProgressBar - 进度条组件
    - VideoPlayer - 视频播放器组件
    - VideoThumbnail - 视频缩略图组件
    - WatermarkCanvas - 水印标记画布组件

- [ ] 10. 测试和优化
  - [ ] 10.1 后端功能测试
    - 测试视频上传（不同格式、大小）
    - 测试批量上传（并发控制）
    - 测试URL下载（不同视频网站）
    - 测试水印标记（单个、多个区域）
    - 测试水印去除（不同裁剪参数）
    - 测试批量处理（多个视频）
    
  - [ ] 10.2 前端功能测试
    - 测试所有页面路由
    - 测试文件上传交互
    - 测试水印标记交互
    - 测试WebSocket实时更新
    - 测试批量操作
    
  - [ ] 10.3 错误处理
    - 添加文件格式验证
    - 添加文件大小限制
    - 添加URL有效性检查
    - 添加FFmpeg错误处理
    - 添加前端错误提示
    
  - [ ] 10.4 性能优化
    - 实现视频处理队列
    - 优化大文件上传（分片上传）
    - 优化视频帧提取速度
    - 添加缓存机制

- [ ] 11. 部署准备
  - [ ] 11.1 后端部署配置
    - 创建Dockerfile（后端）
    - 创建docker-compose.yml
    - 配置环境变量
    - 创建启动脚本
    
  - [ ] 11.2 前端构建配置
    - 配置生产环境构建
    - 优化打包体积
    - 配置Nginx部署
    
  - [ ] 11.3 编写文档
    - 编写README.md（安装、使用说明）
    - 编写API文档
    - 编写部署文档
    - 编写常见问题FAQ

## 项目结构

```
video-watermark-remover/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI应用入口
│   │   ├── models.py          # Pydantic数据模型
│   │   ├── database.py        # 数据库配置
│   │   ├── crud.py            # 数据库CRUD操作
│   │   ├── video_import.py    # 视频导入
│   │   ├── watermark_detection.py  # 水印检测
│   │   ├── watermark_removal.py    # 水印去除
│   │   ├── task_processor.py  # 异步任务处理
│   │   ├── websocket.py       # WebSocket管理
│   │   └── utils.py           # 工具函数
│   ├── uploads/               # 上传的视频
│   ├── outputs/               # 处理后的视频
│   ├── thumbnails/            # 视频缩略图
│   ├── requirements.txt       # Python依赖
│   ├── .env                   # 环境变量
│   ├── Dockerfile            # Docker配置
│   └── run.sh                # 启动脚本
│
├── frontend/                  # 前端项目
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   │   ├── VideoList.tsx
│   │   │   ├── VideoUpload.tsx
│   │   │   ├── WatermarkMarker.tsx
│   │   │   ├── WatermarkRemoval.tsx
│   │   │   ├── BatchProcessing.tsx
│   │   │   └── TaskManager.tsx
│   │   ├── components/       # 通用组件
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── VideoPlayer.tsx
│   │   │   ├── VideoThumbnail.tsx
│   │   │   └── WatermarkCanvas.tsx
│   │   ├── services/         # API服务
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── hooks/            # 自定义Hooks
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useVideoUpload.ts
│   │   │   ├── useTaskProgress.ts
│   │   │   └── useVideoList.ts
│   │   ├── types/            # TypeScript类型
│   │   │   └── index.ts
│   │   ├── App.tsx           # 根组件
│   │   └── main.tsx          # 入口文件
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── index.html
│
├── docker-compose.yml         # Docker编排
└── README.md                 # 项目文档
```

## 技术要点

### 后端技术
1. **FastAPI应用**：使用FastAPI构建RESTful API，支持异步处理
2. **视频处理**：使用FFmpeg进行视频裁剪和格式转换
3. **视频下载**：使用yt-dlp支持多平台视频下载
4. **数据存储**：使用SQLite轻量级数据库存储元数据
5. **实时通信**：使用WebSocket推送处理进度和任务状态
6. **异步处理**：使用asyncio实现并发视频处理

### 前端技术
1. **React 18**：使用最新的React特性（Hooks、Concurrent Mode）
2. **TypeScript**：类型安全，提升代码质量
3. **Vite**：快速的开发服务器和构建工具
4. **Ant Design**：企业级UI组件库，开箱即用
5. **WebSocket**：实时接收后端推送的进度更新
6. **Canvas API**：实现视频帧上的水印标记功能

### 批量处理特性
1. **批量上传**：支持一次上传最多50个视频文件
2. **并发控制**：上传时最多5个文件并行，处理时最多3个视频并行
3. **进度追踪**：通过WebSocket实时推送每个文件的处理进度
4. **错误隔离**：单个文件失败不影响其他文件的处理
5. **批量下载**：支持将处理后的视频打包下载

## 注意事项

- 项目采用前后端分离架构，后端提供API，前端独立部署
- 使用SQLite作为轻量级数据库，适合个人使用，无需复杂配置
- WebSocket用于实时推送进度，提升用户体验
- 批量处理功能通过并发控制避免系统过载
- 前端使用React + TypeScript + Ant Design，提供现代化的用户界面
- 优先实现核心功能，可选的测试任务可以跳过
- 所有视频文件存储在本地文件系统，无需对象存储服务
