import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { message } from 'antd'
import { getTasks, getTaskById } from '@/services/api'
import type { ProcessingTask } from '@/types'

interface TaskContextType {
  // 任务状态
  tasks: ProcessingTask[]
  activeTasks: ProcessingTask[]
  loading: boolean
  
  // 任务进度映射 (taskId -> progress)
  taskProgress: Map<string, number>
  
  // 任务结果映射 (taskId -> result)
  taskResults: Map<string, any>
  
  // 操作方法
  loadTasks: () => Promise<void>
  refreshTasks: () => Promise<void>
  getTask: (taskId: string) => Promise<ProcessingTask | null>
  updateTaskProgress: (taskId: string, progress: number) => void
  updateTaskStatus: (taskId: string, status: ProcessingTask['status'], result?: any, error?: string) => void
  clearCompletedTasks: () => void
  getTasksByVideoId: (videoId: string) => ProcessingTask[]
}

const TaskContext = createContext<TaskContextType | undefined>(undefined)

interface TaskProviderProps {
  children: ReactNode
}

/**
 * 任务状态管理 Context Provider
 * 管理处理任务的状态、进度和结果
 */
export const TaskProvider: React.FC<TaskProviderProps> = ({ children }) => {
  const [tasks, setTasks] = useState<ProcessingTask[]>([])
  const [loading, setLoading] = useState(false)
  const [taskProgress, setTaskProgress] = useState<Map<string, number>>(new Map())
  const [taskResults, setTaskResults] = useState<Map<string, any>>(new Map())

  /**
   * 获取活跃任务（pending 或 processing 状态）
   */
  const activeTasks = tasks.filter(
    task => task.status === 'pending' || task.status === 'processing'
  )

  /**
   * 加载任务列表
   */
  const loadTasks = useCallback(async () => {
    setLoading(true)
    try {
      const response = await getTasks()
      setTasks(response.tasks || [])
      
      // 初始化进度映射
      const progressMap = new Map<string, number>()
      const resultsMap = new Map<string, any>()
      
      response.tasks?.forEach((task: ProcessingTask) => {
        // 根据任务状态设置进度
        if (task.status === 'completed') {
          progressMap.set(task.task_id, 100)
          if (task.result) {
            resultsMap.set(task.task_id, task.result)
          }
        } else if (task.status === 'processing') {
          // 保留现有进度或设置为50%
          const currentProgress = taskProgress.get(task.task_id) || 50
          progressMap.set(task.task_id, currentProgress)
        } else if (task.status === 'pending') {
          progressMap.set(task.task_id, 0)
        } else if (task.status === 'failed') {
          progressMap.set(task.task_id, 0)
        }
      })
      
      setTaskProgress(progressMap)
      setTaskResults(resultsMap)
    } catch (error) {
      console.error('Failed to load tasks:', error)
      message.error('加载任务列表失败')
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [taskProgress])

  /**
   * 刷新任务列表
   */
  const refreshTasks = useCallback(async () => {
    await loadTasks()
  }, [loadTasks])

  /**
   * 获取单个任务详情
   */
  const getTask = useCallback(async (taskId: string): Promise<ProcessingTask | null> => {
    try {
      // 先从缓存中查找
      const cachedTask = tasks.find(t => t.task_id === taskId)
      if (cachedTask) {
        return cachedTask
      }
      
      // 从API获取
      const task = await getTaskById(taskId)
      
      // 更新任务列表
      setTasks(prev => {
        const exists = prev.some(t => t.task_id === taskId)
        if (exists) {
          return prev.map(t => t.task_id === taskId ? task : t)
        }
        return [...prev, task]
      })
      
      return task
    } catch (error) {
      console.error('Failed to get task:', error)
      message.error('获取任务信息失败')
      return null
    }
  }, [tasks])

  /**
   * 更新任务进度
   */
  const updateTaskProgress = useCallback((taskId: string, progress: number) => {
    setTaskProgress(prev => {
      const newMap = new Map(prev)
      newMap.set(taskId, Math.min(100, Math.max(0, progress)))
      return newMap
    })
  }, [])

  /**
   * 更新任务状态
   */
  const updateTaskStatus = useCallback((
    taskId: string, 
    status: ProcessingTask['status'], 
    result?: any,
    error?: string
  ) => {
    setTasks(prev => prev.map(task => {
      if (task.task_id === taskId) {
        const updatedTask = {
          ...task,
          status,
          error_message: error,
          result: result || task.result,
        }
        
        // 更新完成时间
        if (status === 'completed' || status === 'failed') {
          updatedTask.completed_at = new Date().toISOString()
        }
        
        return updatedTask
      }
      return task
    }))
    
    // 更新进度
    if (status === 'completed') {
      updateTaskProgress(taskId, 100)
      if (result) {
        setTaskResults(prev => {
          const newMap = new Map(prev)
          newMap.set(taskId, result)
          return newMap
        })
      }
    } else if (status === 'failed') {
      updateTaskProgress(taskId, 0)
    }
  }, [updateTaskProgress])

  /**
   * 清除已完成的任务
   */
  const clearCompletedTasks = useCallback(() => {
    setTasks(prev => prev.filter(task => 
      task.status !== 'completed' && task.status !== 'failed'
    ))
    
    // 清理进度和结果映射
    setTaskProgress(prev => {
      const newMap = new Map(prev)
      tasks.forEach(task => {
        if (task.status === 'completed' || task.status === 'failed') {
          newMap.delete(task.task_id)
        }
      })
      return newMap
    })
    
    setTaskResults(prev => {
      const newMap = new Map(prev)
      tasks.forEach(task => {
        if (task.status === 'completed' || task.status === 'failed') {
          newMap.delete(task.task_id)
        }
      })
      return newMap
    })
    
    message.success('已清除完成的任务')
  }, [tasks])

  /**
   * 根据视频ID获取相关任务
   */
  const getTasksByVideoId = useCallback((videoId: string): ProcessingTask[] => {
    return tasks.filter(task => task.video_id === videoId)
  }, [tasks])

  const value: TaskContextType = {
    tasks,
    activeTasks,
    loading,
    taskProgress,
    taskResults,
    loadTasks,
    refreshTasks,
    getTask,
    updateTaskProgress,
    updateTaskStatus,
    clearCompletedTasks,
    getTasksByVideoId,
  }

  return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>
}

/**
 * 使用任务 Context 的 Hook
 */
export const useTaskContext = (): TaskContextType => {
  const context = useContext(TaskContext)
  if (context === undefined) {
    throw new Error('useTaskContext must be used within a TaskProvider')
  }
  return context
}
