import { useState, useEffect } from 'react'
import { useWebSocket } from './useWebSocket'
import api from '@/services/api'
import type { ProcessingTask } from '@/types'

/**
 * 任务进度 Hook
 * 实时监控任务处理进度
 */
export const useTaskProgress = (taskId?: string) => {
  const [task, setTask] = useState<ProcessingTask | null>(null)
  const [progress, setProgress] = useState(0)
  const [loading, setLoading] = useState(false)

  // WebSocket连接用于实时更新
  useWebSocket(
    `ws://localhost:8000/ws/tasks/${taskId}`,
    {
      onMessage: (data) => {
        if (data.task_id === taskId) {
          setTask(data.task)
          setProgress(data.progress || 0)
        }
      },
    }
  )

  // 初始加载任务信息
  useEffect(() => {
    if (taskId) {
      loadTask()
    }
  }, [taskId])

  const loadTask = async () => {
    if (!taskId) return

    setLoading(true)
    try {
      const response = await api.get(`/tasks/${taskId}`)
      setTask(response.data)
      
      // 根据任务状态设置进度
      if (response.data.status === 'completed') {
        setProgress(100)
      } else if (response.data.status === 'processing') {
        setProgress(50)
      } else {
        setProgress(0)
      }
    } catch (error) {
      console.error('Failed to load task:', error)
    } finally {
      setLoading(false)
    }
  }

  const refreshTask = () => {
    loadTask()
  }

  return {
    task,
    progress,
    loading,
    refreshTask,
  }
}
