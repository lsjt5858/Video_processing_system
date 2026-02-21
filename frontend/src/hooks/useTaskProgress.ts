import { useState, useEffect, useCallback } from 'react'
import { useWebSocketContext } from '@/contexts/WebSocketContext'
import { getTaskStatus } from '@/services/api'
import type { ProcessingTask } from '@/types'

/**
 * 任务进度 Hook
 * 实时监控任务处理进度
 */
export const useTaskProgress = (taskId?: string) => {
  const [task, setTask] = useState<ProcessingTask | null>(null)
  const [progress, setProgress] = useState(0)
  const [loading, setLoading] = useState(false)
  
  const { subscribe, isConnected } = useWebSocketContext()

  // 订阅 WebSocket 消息更新任务状态
  useEffect(() => {
    if (!taskId) return

    const unsubProgress = subscribe('task_progress', (data: any) => {
      if (data.task_id === taskId) {
        setTask((prev: ProcessingTask | null) => prev ? { ...prev, status: data.status } : null)
        setProgress(data.progress || 0)
      }
    })

    const unsubCompleted = subscribe('task_completed', (data: any) => {
      if (data.task_id === taskId) {
        setTask((prev: ProcessingTask | null) => prev ? { 
          ...prev, 
          status: 'completed', 
          result: data.result 
        } : null)
        setProgress(100)
      }
    })

    const unsubFailed = subscribe('task_failed', (data: any) => {
      if (data.task_id === taskId) {
        setTask((prev: ProcessingTask | null) => prev ? { 
          ...prev, 
          status: 'failed', 
          error_message: data.error 
        } : null)
      }
    })

    return () => {
      unsubProgress()
      unsubCompleted()
      unsubFailed()
    }
  }, [taskId, subscribe])

  // 初始加载任务信息
  useEffect(() => {
    if (taskId) {
      loadTask()
    }
  }, [taskId])

  const loadTask = useCallback(async () => {
    if (!taskId) return

    setLoading(true)
    try {
      const response = await getTaskStatus(taskId)
      setTask(response)
      
      if (response.status === 'completed') {
        setProgress(100)
      } else if (response.status === 'processing') {
        setProgress(50)
      } else {
        setProgress(0)
      }
    } catch (error) {
      console.error('Failed to load task:', error)
    } finally {
      setLoading(false)
    }
  }, [taskId])

  const refreshTask = () => {
    loadTask()
  }

  return {
    task,
    progress,
    loading,
    refreshTask,
    isConnected,
  }
}
