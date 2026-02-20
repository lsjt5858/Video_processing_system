import { useState } from 'react'
import { message } from 'antd'
import api from '@/services/api'

interface UploadProgress {
  percent: number
  status: 'uploading' | 'success' | 'error'
}

/**
 * 视频上传 Hook
 * 处理视频文件上传逻辑
 */
export const useVideoUpload = () => {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState<UploadProgress>({
    percent: 0,
    status: 'uploading',
  })

  const uploadVideo = async (file: File) => {
    setUploading(true)
    setProgress({ percent: 0, status: 'uploading' })

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/videos/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          )
          setProgress({ percent, status: 'uploading' })
        },
      })

      setProgress({ percent: 100, status: 'success' })
      message.success('上传成功')
      return response.data
    } catch (error) {
      setProgress({ percent: 0, status: 'error' })
      message.error('上传失败')
      throw error
    } finally {
      setUploading(false)
    }
  }

  const uploadMultipleVideos = async (files: File[]) => {
    const results = []
    for (const file of files) {
      try {
        const result = await uploadVideo(file)
        results.push({ file, result, success: true })
      } catch (error) {
        results.push({ file, error, success: false })
      }
    }
    return results
  }

  return {
    uploading,
    progress,
    uploadVideo,
    uploadMultipleVideos,
  }
}
