# 状态管理 Context

本目录包含应用的全局状态管理 Context，使用 React Context API 实现。

## 架构概述

应用使用三个主要的 Context 来管理不同领域的状态：

1. **VideoContext** - 视频列表和视频相关状态
2. **TaskContext** - 处理任务状态和进度
3. **WebSocketContext** - WebSocket 连接和实时消息

## Context 详解

### 1. VideoContext

管理视频列表、筛选、分页和选中状态。

**提供的状态：**
- `videos`: 视频列表
- `loading`: 加载状态
- `currentPage`: 当前页码
- `total`: 总视频数
- `pageSize`: 每页大小
- `filters`: 筛选条件
- `selectedVideos`: 选中的视频ID列表

**提供的方法：**
- `loadVideos()`: 加载视频列表
- `refreshVideos()`: 刷新视频列表
- `deleteVideo(videoId)`: 删除视频
- `getVideo(videoId)`: 获取单个视频详情
- `setCurrentPage(page)`: 设置当前页
- `setPageSize(size)`: 设置每页大小
- `updateFilters(filters)`: 更新筛选条件
- `clearFilters()`: 清除筛选条件
- `setSelectedVideos(videoIds)`: 设置选中的视频
- `addSelectedVideo(videoId)`: 添加选中的视频
- `removeSelectedVideo(videoId)`: 移除选中的视频
- `clearSelectedVideos()`: 清除所有选中

**使用示例：**

```tsx
import { useVideoContext } from '@/contexts'

function VideoList() {
  const { 
    videos, 
    loading, 
    currentPage, 
    total, 
    loadVideos,
    deleteVideo 
  } = useVideoContext()

  useEffect(() => {
    loadVideos()
  }, [currentPage])

  return (
    <div>
      {videos.map(video => (
        <div key={video.video_id}>
          {video.storage_path}
          <button onClick={() => deleteVideo(video.video_id)}>删除</button>
        </div>
      ))}
    </div>
  )
}
```

### 2. TaskContext

管理处理任务的状态、进度和结果。

**提供的状态：**
- `tasks`: 所有任务列表
- `activeTasks`: 活跃任务（pending 或 processing）
- `loading`: 加载状态
- `taskProgress`: 任务进度映射 (taskId -> progress)
- `taskResults`: 任务结果映射 (taskId -> result)

**提供的方法：**
- `loadTasks()`: 加载任务列表
- `refreshTasks()`: 刷新任务列表
- `getTask(taskId)`: 获取单个任务详情
- `updateTaskProgress(taskId, progress)`: 更新任务进度
- `updateTaskStatus(taskId, status, result?, error?)`: 更新任务状态
- `clearCompletedTasks()`: 清除已完成的任务
- `getTasksByVideoId(videoId)`: 获取视频相关的任务

**使用示例：**

```tsx
import { useTaskContext } from '@/contexts'

function TaskManager() {
  const { 
    tasks, 
    activeTasks,
    taskProgress,
    updateTaskProgress 
  } = useTaskContext()

  return (
    <div>
      <h2>活跃任务: {activeTasks.length}</h2>
      {tasks.map(task => (
        <div key={task.task_id}>
          {task.task_type}: {taskProgress.get(task.task_id) || 0}%
        </div>
      ))}
    </div>
  )
}
```

### 3. WebSocketContext

管理 WebSocket 连接、消息队列和事件订阅。

**提供的状态：**
- `isConnected`: 是否已连接
- `connectionStatus`: 连接状态 ('connecting' | 'connected' | 'disconnected' | 'error')
- `lastMessage`: 最后收到的消息
- `messageQueue`: 消息队列（离线时缓存）

**提供的方法：**
- `sendMessage(type, data)`: 发送消息
- `subscribe(type, callback)`: 订阅特定类型的消息，返回取消订阅函数
- `connect()`: 连接 WebSocket
- `disconnect()`: 断开连接
- `clearMessageQueue()`: 清除消息队列

**使用示例：**

```tsx
import { useWebSocketContext } from '@/contexts'
import { useEffect } from 'react'

function VideoUpload() {
  const { isConnected, subscribe } = useWebSocketContext()

  useEffect(() => {
    // 订阅上传进度消息
    const unsubscribe = subscribe('upload_progress', (data) => {
      console.log('Upload progress:', data.progress)
    })

    // 组件卸载时取消订阅
    return unsubscribe
  }, [subscribe])

  return (
    <div>
      连接状态: {isConnected ? '已连接' : '未连接'}
    </div>
  )
}
```

## 集成 WebSocket 和 Task 更新

结合 WebSocketContext 和 TaskContext 实现实时任务进度更新：

```tsx
import { useWebSocketContext, useTaskContext } from '@/contexts'
import { useEffect } from 'react'

function TaskProgressMonitor() {
  const { subscribe } = useWebSocketContext()
  const { updateTaskProgress, updateTaskStatus } = useTaskContext()

  useEffect(() => {
    // 订阅任务进度更新
    const unsubscribeProgress = subscribe('task_progress', (data) => {
      updateTaskProgress(data.task_id, data.progress)
    })

    // 订阅任务完成
    const unsubscribeComplete = subscribe('task_complete', (data) => {
      updateTaskStatus(data.task_id, 'completed', data.result)
    })

    // 订阅任务失败
    const unsubscribeFailed = subscribe('task_failed', (data) => {
      updateTaskStatus(data.task_id, 'failed', undefined, data.error)
    })

    return () => {
      unsubscribeProgress()
      unsubscribeComplete()
      unsubscribeFailed()
    }
  }, [subscribe, updateTaskProgress, updateTaskStatus])

  return null // 这是一个监听组件，不渲染UI
}
```

## 最佳实践

### 1. 避免不必要的重渲染

使用 `useCallback` 和 `useMemo` 优化性能：

```tsx
const { videos } = useVideoContext()

const filteredVideos = useMemo(() => {
  return videos.filter(v => v.format === 'mp4')
}, [videos])
```

### 2. 条件性加载数据

只在需要时加载数据：

```tsx
function VideoDetail({ videoId }: { videoId: string }) {
  const { getVideo } = useVideoContext()
  const [video, setVideo] = useState(null)

  useEffect(() => {
    getVideo(videoId).then(setVideo)
  }, [videoId, getVideo])

  return <div>{video?.storage_path}</div>
}
```

### 3. 清理订阅

始终在组件卸载时清理 WebSocket 订阅：

```tsx
useEffect(() => {
  const unsubscribe = subscribe('message_type', handleMessage)
  return unsubscribe // 自动清理
}, [subscribe])
```

### 4. 错误处理

Context 方法内部已包含错误处理，但可以添加额外的错误边界：

```tsx
import { ErrorBoundary } from 'react-error-boundary'

function App() {
  return (
    <ErrorBoundary fallback={<div>出错了</div>}>
      <VideoProvider>
        <YourComponent />
      </VideoProvider>
    </ErrorBoundary>
  )
}
```

## 迁移指南

### 从 Hook 迁移到 Context

**之前（使用 Hook）：**

```tsx
function VideoList() {
  const { videos, loading, loadVideos } = useVideoList()
  
  useEffect(() => {
    loadVideos()
  }, [])
  
  return <div>...</div>
}
```

**之后（使用 Context）：**

```tsx
function VideoList() {
  const { videos, loading, loadVideos } = useVideoContext()
  
  useEffect(() => {
    loadVideos()
  }, [])
  
  return <div>...</div>
}
```

主要变化：
1. 导入从 `@/hooks/useVideoList` 改为 `@/contexts`
2. Hook 名称从 `useVideoList` 改为 `useVideoContext`
3. API 基本保持一致

## 性能考虑

### Context 分离

我们将状态分为三个独立的 Context，而不是一个大的全局状态，原因：

1. **减少重渲染**：只有使用特定 Context 的组件会在该 Context 更新时重渲染
2. **关注点分离**：每个 Context 负责特定领域的状态
3. **更好的代码组织**：相关的状态和逻辑集中在一起

### 何时使用 Context vs Hook

- **使用 Context**：需要跨多个组件共享状态时
- **使用 Hook**：状态只在单个组件或其子组件中使用时

## 故障排除

### 1. "useXxxContext must be used within a XxxProvider"

**原因**：组件没有被相应的 Provider 包裹

**解决**：确保在 App.tsx 中正确包裹了 Provider

### 2. WebSocket 连接失败

**检查**：
- 后端 WebSocket 服务是否运行
- URL 是否正确（默认 `ws://localhost:8000/ws`）
- 浏览器控制台是否有错误信息

### 3. 状态更新不生效

**检查**：
- 是否正确调用了更新方法
- 是否在 useEffect 的依赖数组中包含了必要的依赖
- 浏览器 React DevTools 中查看 Context 值

## 未来改进

可能的改进方向：

1. **持久化状态**：使用 localStorage 或 IndexedDB 持久化部分状态
2. **状态同步**：多标签页之间同步状态
3. **性能优化**：使用 Context Selector 减少不必要的重渲染
4. **TypeScript 增强**：更严格的类型定义
5. **测试覆盖**：添加 Context 的单元测试

## 参考资料

- [React Context API](https://react.dev/reference/react/useContext)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [React Performance Optimization](https://react.dev/learn/render-and-commit)
