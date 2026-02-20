// 视频格式
export type VideoFormat = 'mp4' | 'avi' | 'mov' | 'mkv'

// 任务状态
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

// 处理模式
export type ProcessingMode = 'crop_reconstruct' | 'ai_inpainting' | 'blur_replace'

// 视频元数据
export interface VideoMetadata {
  video_id: string
  format: VideoFormat
  resolution: [number, number] // [width, height]
  duration: number // 秒
  codec: string
  framerate: number
  bitrate: number
  file_size: number
  created_at: string
}

// 边界框
export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

// 水印区域
export interface WatermarkRegion {
  region_id: string
  video_id: string
  bbox: BoundingBox
  start_time: number
  end_time: number
  confidence: number
  watermark_type: string
  detection_method: 'auto' | 'manual'
}

// 视频信息
export interface Video {
  video_id: string
  user_id: string
  format: VideoFormat
  resolution: {
    width: number
    height: number
  }
  duration: number
  codec: string
  framerate: number
  bitrate: number
  file_size: number
  storage_path: string
  import_source: 'local' | 'platform' | 'url'
  created_at: string
  // 可选的关联数据
  metadata?: VideoMetadata
  watermark_regions?: WatermarkRegion[]
  processing_tasks?: ProcessingTask[]
}

// 处理任务
export interface ProcessingTask {
  task_id: string
  user_id: string
  video_id: string
  task_type: string
  status: TaskStatus
  parameters: Record<string, any>
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  result?: Record<string, any>
}

// API响应
export interface ApiResponse<T = any> {
  data?: T
  error?: {
    code: string
    message: string
    details?: any
  }
}
