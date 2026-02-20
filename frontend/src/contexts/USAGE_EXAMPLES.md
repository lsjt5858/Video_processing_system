# Context 使用示例

本文档提供实际的代码示例，展示如何在组件中使用新的 Context 状态管理系统。

## 示例 1: 视频列表页面（使用 VideoContext）

```tsx
import React, { useEffect } from 'react'
import { Table, Button, Space, message } from 'antd'
import { useVideoContext } from '@/contexts'
import { useNavigate } from 'react-router-dom'

function VideoListPage() {
  const navigate = useNavigate()
  const {
    videos,
    loading,
    currentPage,
    total,
    pageSize,
    loadVideos,
    deleteVideo,
    setCurrentPage,
  } = useVideoContext()

  // 组件挂载时加载视频列表
  useEffect(() => {
    loadVideos()
  }, [currentPage, pageSize])

  const handleDelete = async (videoId: string) => {
    try {
      await deleteVideo(videoId)
      message.success('删除成功')
    } catch (error) {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'storage_path',
      key: 'storage_path',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button onClick={() => navigate(`/video/${record.video_id}`)}>
            查看
          </Button>
          <Button danger onClick={() => handleDelete(record.video_id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Table
      columns={columns}
      dataSource={videos}
      loading={loading}
      rowKey="video_id"
      pagination={{
        current: currentPage,
        pageSize: pageSize,
        total: total,
        onChange: setCurrentPage,
      }}
    />
  )
}

export default VideoListPage
```

## 示例 2: 任务监控组件（使用 TaskContext + WebSocketContext）

```tsx
import React, { useEffect } from 'react'
import { Progress, Card, Tag } from 'antd'
import { useTaskContext, useWebSocketContext } from '@/contexts'

function TaskMonitor() {
  const { 
    activeTasks, 
    taskProgress, 
    updateTaskProgress, 
    updateTaskStatus 
  } = useTaskContext()
  
  const { subscribe, isConnected } = useWebSocketContext()

  // 订阅 WebSocket 消息更新任务状态
  useEffect(() => {
    // 订阅任务进度更新
    const unsubProgress = subscribe('task_progress', (data) => {
      updateTaskProgress(data.task_id, data.progress)
    })

    // 订阅任务完成
    const unsubComplete = subscribe('task_complete', (data) => {
      updateTaskStatus(data.task_id, 'completed', data.result)
    })

    // 订阅任务失败
    const unsubFailed = subscribe('task_failed', (data) => {
      updateTaskStatus(data.task_id, 'failed', undefined, data.error)
    })

    // 清理订阅
    return () => {
      unsubProgress()
      unsubComplete()
      unsubFailed()
    }
  }, [subscribe, updateTaskProgress, updateTaskStatus])

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        WebSocket 状态: {isConnected ? 
          <Tag color="green">已连接</Tag> : 
          <Tag color="red">未连接</Tag>
        }
      </div>
      
      <div>
        <h3>活跃任务 ({activeTasks.length})</h3>
        {activeTasks.map(task => (
          <Card key={task.task_id} style={{ marginBottom: 16 }}>
            <div>任务ID: {task.task_id}</div>
            <div>类型: {task.task_type}</div>
            <div>状态: {task.status}</div>
            <Progress 
              percent={taskProgress.get(task.task_id) || 0} 
              status={task.status === 'failed' ? 'exception' : 'active'}
            />
          </Card>
        ))}
      </div>
    </div>
  )
}

export default TaskMonitor
```

## 示例 3: 批量选择视频（使用 VideoContext 的选择功能）

```tsx
import React, { useEffect } from 'react'
import { Table, Button, Space, message } from 'antd'
import { useVideoContext } from '@/contexts'

function BatchVideoSelector() {
  const {
    videos,
    loading,
    selectedVideos,
    loadVideos,
    setSelectedVideos,
    clearSelectedVideos,
  } = useVideoContext()

  useEffect(() => {
    loadVideos()
  }, [])

  const rowSelection = {
    selectedRowKeys: selectedVideos,
    onChange: (selectedRowKeys: React.Key[]) => {
      setSelectedVideos(selectedRowKeys as string[])
    },
  }

  const handleBatchProcess = () => {
    if (selectedVideos.length === 0) {
      message.warning('请先选择视频')
      return
    }
    
    console.log('批量处理视频:', selectedVideos)
    // 执行批量处理逻辑...
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button 
          type="primary" 
          onClick={handleBatchProcess}
          disabled={selectedVideos.length === 0}
        >
          批量处理 ({selectedVideos.length})
        </Button>
        <Button onClick={clearSelectedVideos}>
          清除选择
        </Button>
      </Space>

      <Table
        rowSelection={rowSelection}
        columns={[
          { title: '文件名', dataIndex: 'storage_path', key: 'storage_path' },
          { title: '格式', dataIndex: 'format', key: 'format' },
        ]}
        dataSource={videos}
        loading={loading}
        rowKey="video_id"
      />
    </div>
  )
}

export default BatchVideoSelector
```

## 示例 4: 视频上传进度（使用 WebSocketContext）

```tsx
import React, { useState, useEffect } from 'react'
import { Upload, Progress, message } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { useWebSocketContext } from '@/contexts'
import { uploadVideo } from '@/services/api'

function VideoUploader() {
  const { subscribe } = useWebSocketContext()
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    // 订阅上传进度
    const unsubscribe = subscribe('upload_progress', (data) => {
      setProgress(data.progress)
    })

    return unsubscribe
  }, [subscribe])

  const handleUpload = async (file: File) => {
    setUploading(true)
    setProgress(0)

    try {
      await uploadVideo(file, (progress) => {
        setProgress(progress)
      })
      message.success('上传成功')
    } catch (error) {
      message.error('上传失败')
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  return (
    <div>
      <Upload
        beforeUpload={(file) => {
          handleUpload(file)
          return false // 阻止自动上传
        }}
        showUploadList={false}
      >
        <Button icon={<UploadOutlined />} loading={uploading}>
          选择视频
        </Button>
      </Upload>

      {uploading && (
        <Progress 
          percent={progress} 
          status="active"
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  )
}

export default VideoUploader
```

## 示例 5: 视频详情页（组合使用多个 Context）

```tsx
import React, { useEffect, useState } from 'react'
import { Card, Descriptions, Button, Space, Spin } from 'antd'
import { useParams } from 'react-router-dom'
import { useVideoContext, useTaskContext } from '@/contexts'
import type { Video } from '@/types'

function VideoDetailPage() {
  const { videoId } = useParams<{ videoId: string }>()
  const { getVideo } = useVideoContext()
  const { getTasksByVideoId } = useTaskContext()
  
  const [video, setVideo] = useState<Video | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (videoId) {
      loadVideoDetail()
    }
  }, [videoId])

  const loadVideoDetail = async () => {
    if (!videoId) return
    
    setLoading(true)
    try {
      const videoData = await getVideo(videoId)
      setVideo(videoData)
    } catch (error) {
      console.error('Failed to load video:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Spin size="large" />
  }

  if (!video) {
    return <div>视频不存在</div>
  }

  const relatedTasks = getTasksByVideoId(videoId!)

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Card title="视频信息">
        <Descriptions bordered>
          <Descriptions.Item label="视频ID">
            {video.video_id}
          </Descriptions.Item>
          <Descriptions.Item label="格式">
            {video.format}
          </Descriptions.Item>
          <Descriptions.Item label="分辨率">
            {video.resolution.width} × {video.resolution.height}
          </Descriptions.Item>
          <Descriptions.Item label="时长">
            {video.duration.toFixed(2)} 秒
          </Descriptions.Item>
          <Descriptions.Item label="文件大小">
            {(video.file_size / 1024 / 1024).toFixed(2)} MB
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="相关任务">
        {relatedTasks.length === 0 ? (
          <div>暂无相关任务</div>
        ) : (
          relatedTasks.map(task => (
            <Card key={task.task_id} type="inner" style={{ marginBottom: 8 }}>
              <div>任务类型: {task.task_type}</div>
              <div>状态: {task.status}</div>
              <div>创建时间: {task.created_at}</div>
            </Card>
          ))
        )}
      </Card>
    </Space>
  )
}

export default VideoDetailPage
```

## 示例 6: 全局任务进度监听器（放在 App 或 Layout 中）

```tsx
import React, { useEffect } from 'react'
import { message } from 'antd'
import { useTaskContext, useWebSocketContext } from '@/contexts'

/**
 * 全局任务进度监听器
 * 这个组件不渲染任何UI，只负责监听 WebSocket 消息并更新任务状态
 * 应该放在 App.tsx 或 Layout 组件中
 */
function GlobalTaskListener() {
  const { updateTaskProgress, updateTaskStatus, refreshTasks } = useTaskContext()
  const { subscribe, isConnected } = useWebSocketContext()

  useEffect(() => {
    if (!isConnected) return

    // 订阅所有任务相关的消息
    const unsubscribers = [
      subscribe('task_progress', (data) => {
        updateTaskProgress(data.task_id, data.progress)
      }),

      subscribe('task_complete', (data) => {
        updateTaskStatus(data.task_id, 'completed', data.result)
        message.success(`任务 ${data.task_id.slice(0, 8)} 已完成`)
        refreshTasks()
      }),

      subscribe('task_failed', (data) => {
        updateTaskStatus(data.task_id, 'failed', undefined, data.error)
        message.error(`任务 ${data.task_id.slice(0, 8)} 失败: ${data.error}`)
        refreshTasks()
      }),

      subscribe('task_started', (data) => {
        updateTaskStatus(data.task_id, 'processing')
        refreshTasks()
      }),
    ]

    // 清理所有订阅
    return () => {
      unsubscribers.forEach(unsub => unsub())
    }
  }, [isConnected, subscribe, updateTaskProgress, updateTaskStatus, refreshTasks])

  return null // 不渲染任何内容
}

export default GlobalTaskListener
```

## 示例 7: 在 Layout 中集成监听器

```tsx
import React from 'react'
import { Layout } from 'antd'
import { Outlet } from 'react-router-dom'
import GlobalTaskListener from './GlobalTaskListener'

const { Header, Content } = Layout

function AppLayout() {
  return (
    <Layout>
      {/* 全局任务监听器 */}
      <GlobalTaskListener />
      
      <Header>
        <h1>一键美</h1>
      </Header>
      
      <Content style={{ padding: '24px' }}>
        <Outlet />
      </Content>
    </Layout>
  )
}

export default AppLayout
```

## 最佳实践总结

### 1. 数据加载时机

```tsx
// ✅ 好的做法：在 useEffect 中加载数据
useEffect(() => {
  loadVideos()
}, [currentPage]) // 依赖项变化时重新加载

// ❌ 不好的做法：在渲染时直接调用
loadVideos() // 会导致无限循环
```

### 2. 清理副作用

```tsx
// ✅ 好的做法：返回清理函数
useEffect(() => {
  const unsubscribe = subscribe('message', handler)
  return unsubscribe // 组件卸载时自动清理
}, [subscribe])

// ❌ 不好的做法：不清理订阅
useEffect(() => {
  subscribe('message', handler)
  // 没有返回清理函数，会导致内存泄漏
}, [subscribe])
```

### 3. 条件性使用 Context

```tsx
// ✅ 好的做法：只在需要时使用 Context
function VideoList() {
  const { videos, loading } = useVideoContext()
  // 只使用需要的状态
}

// ❌ 不好的做法：解构所有状态
function VideoList() {
  const { 
    videos, loading, currentPage, total, pageSize, filters,
    selectedVideos, loadVideos, refreshVideos, deleteVideo,
    getVideo, setCurrentPage, setPageSize, updateFilters,
    clearFilters, setSelectedVideos, addSelectedVideo,
    removeSelectedVideo, clearSelectedVideos 
  } = useVideoContext()
  // 解构了很多不需要的状态和方法
}
```

### 4. 错误处理

```tsx
// ✅ 好的做法：处理异步操作的错误
const handleDelete = async (videoId: string) => {
  try {
    await deleteVideo(videoId)
    message.success('删除成功')
  } catch (error) {
    message.error('删除失败')
    console.error(error)
  }
}

// ❌ 不好的做法：不处理错误
const handleDelete = async (videoId: string) => {
  await deleteVideo(videoId) // 如果失败会导致未捕获的异常
  message.success('删除成功')
}
```

## 性能优化技巧

### 1. 使用 useMemo 缓存计算结果

```tsx
const { videos } = useVideoContext()

const mp4Videos = useMemo(() => {
  return videos.filter(v => v.format === 'mp4')
}, [videos])
```

### 2. 使用 useCallback 缓存回调函数

```tsx
const { deleteVideo } = useVideoContext()

const handleDelete = useCallback((videoId: string) => {
  deleteVideo(videoId)
}, [deleteVideo])
```

### 3. 避免不必要的重渲染

```tsx
// 使用 React.memo 包装组件
const VideoItem = React.memo(({ video }: { video: Video }) => {
  return <div>{video.storage_path}</div>
})
```

这些示例展示了如何在实际项目中使用新的 Context 状态管理系统。根据具体需求，可以灵活组合使用这些模式。
