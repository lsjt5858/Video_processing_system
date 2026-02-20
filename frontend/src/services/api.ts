import axios, { AxiosInstance, AxiosError } from 'axios'
import type { ApiResponse, Video, ProcessingTask } from '@/types'

// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 后端返回格式: { success: true, data: {...} }
    // 直接返回 data 字段
    if (response.data && response.data.success) {
      return response.data.data
    }
    return response.data
  },
  (error: AxiosError<ApiResponse>) => {
    // 统一错误处理
    const errorMessage = error.response?.data?.error?.message || error.message || '请求失败'
    console.error('API Error:', errorMessage)
    return Promise.reject(error)
  }
)

// ==================== 视频相关 API ====================

/**
 * 获取视频列表
 */
export const getVideos = async (params: {
  page?: number
  page_size?: number
  search?: string
  format?: string
  start_date?: string
  end_date?: string
}): Promise<{ videos: Video[]; total: number; pagination: any }> => {
  const response: any = await api.get('/videos', { params })
  // 后端返回: { videos: [...], pagination: { total_count: ... } }
  return {
    videos: response.videos || [],
    total: response.pagination?.total_count || 0,
    pagination: response.pagination
  }
}

/**
 * 获取视频详情
 */
export const getVideoById = async (videoId: string): Promise<Video> => {
  return api.get(`/videos/${videoId}`)
}

/**
 * 删除视频
 */
export const deleteVideo = async (videoId: string): Promise<void> => {
  return api.delete(`/videos/${videoId}`)
}

/**
 * 上传视频
 */
export const uploadVideo = async (file: File, onProgress?: (progress: number) => void): Promise<Video> => {
  const formData = new FormData()
  formData.append('file', file)

  return api.post('/videos/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    },
  })
}

/**
 * 批量上传视频
 */
export const batchUploadVideos = async (files: File[]): Promise<{ results: Video[] }> => {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  return api.post('/videos/batch-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

/**
 * 通过 URL 下载视频
 */
export const downloadVideoFromUrl = async (url: string): Promise<Video> => {
  return api.post('/videos/download', { url })
}

/**
 * 获取视频缩略图
 */
export const getVideoThumbnail = (videoId: string): string => {
  return `/api/videos/${videoId}/thumbnail`
}

/**
 * 下载处理后的视频
 */
export const downloadProcessedVideo = (videoId: string): string => {
  return `/api/videos/${videoId}/output`
}

// ==================== 水印相关 API ====================

/**
 * 获取视频帧
 */
export const getVideoFrames = async (videoId: string): Promise<{ frames: string[] }> => {
  return api.get(`/videos/${videoId}/frames`)
}

/**
 * 标记水印区域
 */
export const markWatermark = async (videoId: string, regions: any[]): Promise<any> => {
  return api.post(`/videos/${videoId}/watermarks`, { regions })
}

/**
 * 获取水印区域列表
 */
export const getWatermarks = async (videoId: string): Promise<any[]> => {
  return api.get(`/videos/${videoId}/watermarks`)
}

/**
 * 更新水印区域
 */
export const updateWatermark = async (videoId: string, regionId: string, bbox: any): Promise<any> => {
  return api.put(`/videos/${videoId}/watermarks/${regionId}`, { bbox })
}

/**
 * 删除水印区域
 */
export const deleteWatermark = async (videoId: string, regionId: string): Promise<void> => {
  return api.delete(`/videos/${videoId}/watermarks/${regionId}`)
}

// ==================== 水印去除相关 API ====================

/**
 * 执行水印去除
 */
export const removeWatermark = async (videoId: string, params: {
  mode: string
  regions: any[]
  custom_logo?: string
}): Promise<ProcessingTask> => {
  return api.post(`/videos/${videoId}/remove`, params)
}

/**
 * 批量水印去除
 */
export const batchRemoveWatermark = async (tasks: any[]): Promise<{ tasks: ProcessingTask[] }> => {
  return api.post('/batch/remove', { tasks })
}

/**
 * 批量检测水印
 */
export const batchDetect = async (videoIds: string[]): Promise<{ results: any[] }> => {
  return api.post('/batch/detect', { video_ids: videoIds })
}

// ==================== 任务相关 API ====================

/**
 * 获取任务状态
 */
export const getTaskStatus = async (taskId: string): Promise<ProcessingTask> => {
  return api.get(`/tasks/${taskId}`)
}

/**
 * 获取任务详情（别名）
 */
export const getTaskById = async (taskId: string): Promise<ProcessingTask> => {
  return getTaskStatus(taskId)
}

/**
 * 获取任务列表
 */
export const getTasks = async (params?: {
  page?: number
  page_size?: number
  status?: string
  task_type?: string
  search?: string
  start_date?: string
  end_date?: string
}): Promise<{ tasks: ProcessingTask[]; total: number }> => {
  const response: any = await api.get('/tasks', { params })
  return {
    tasks: response.tasks || [],
    total: response.pagination?.total_count || response.total || 0
  }
}

export default api
