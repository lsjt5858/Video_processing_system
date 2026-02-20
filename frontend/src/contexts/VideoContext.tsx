import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { message } from 'antd'
import { getVideos, deleteVideo as deleteVideoApi, getVideoById } from '@/services/api'
import type { Video } from '@/types'

interface VideoFilters {
  search?: string
  format?: string
  startDate?: string
  endDate?: string
}

interface VideoContextType {
  // 视频列表状态
  videos: Video[]
  loading: boolean
  currentPage: number
  total: number
  pageSize: number
  filters: VideoFilters
  
  // 选中的视频
  selectedVideos: string[]
  
  // 操作方法
  loadVideos: () => Promise<void>
  refreshVideos: () => Promise<void>
  deleteVideo: (videoId: string) => Promise<void>
  getVideo: (videoId: string) => Promise<Video | null>
  setCurrentPage: (page: number) => void
  setPageSize: (size: number) => void
  updateFilters: (filters: Partial<VideoFilters>) => void
  clearFilters: () => void
  setSelectedVideos: (videoIds: string[]) => void
  addSelectedVideo: (videoId: string) => void
  removeSelectedVideo: (videoId: string) => void
  clearSelectedVideos: () => void
}

const VideoContext = createContext<VideoContextType | undefined>(undefined)

interface VideoProviderProps {
  children: ReactNode
}

/**
 * 视频状态管理 Context Provider
 * 管理视频列表、筛选、分页和选中状态
 */
export const VideoProvider: React.FC<VideoProviderProps> = ({ children }) => {
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize, setPageSize] = useState(20)
  const [filters, setFilters] = useState<VideoFilters>({})
  const [selectedVideos, setSelectedVideos] = useState<string[]>([])

  /**
   * 加载视频列表
   */
  const loadVideos = useCallback(async () => {
    setLoading(true)
    try {
      const response = await getVideos({
        page: currentPage,
        page_size: pageSize,
        search: filters.search,
        format: filters.format,
        start_date: filters.startDate,
        end_date: filters.endDate,
      })
      setVideos(response.videos || [])
      setTotal(response.total || 0)
    } catch (error) {
      console.error('Failed to load videos:', error)
      message.error('加载视频列表失败')
      setVideos([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [currentPage, pageSize, filters])

  /**
   * 刷新视频列表
   */
  const refreshVideos = useCallback(async () => {
    await loadVideos()
  }, [loadVideos])

  /**
   * 删除视频
   */
  const deleteVideo = useCallback(async (videoId: string) => {
    try {
      await deleteVideoApi(videoId)
      message.success('删除成功')
      
      // 从选中列表中移除
      setSelectedVideos(prev => prev.filter(id => id !== videoId))
      
      // 如果当前页只有一个视频且不是第一页，则返回上一页
      if (videos.length === 1 && currentPage > 1) {
        setCurrentPage(currentPage - 1)
      } else {
        await loadVideos()
      }
    } catch (error) {
      console.error('Failed to delete video:', error)
      message.error('删除失败')
    }
  }, [videos.length, currentPage, loadVideos])

  /**
   * 获取单个视频详情
   */
  const getVideo = useCallback(async (videoId: string): Promise<Video | null> => {
    try {
      // 先从缓存中查找
      const cachedVideo = videos.find(v => v.video_id === videoId)
      if (cachedVideo) {
        return cachedVideo
      }
      
      // 从API获取
      const video = await getVideoById(videoId)
      return video
    } catch (error) {
      console.error('Failed to get video:', error)
      message.error('获取视频信息失败')
      return null
    }
  }, [videos])

  /**
   * 更新筛选条件
   */
  const updateFilters = useCallback((newFilters: Partial<VideoFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
    setCurrentPage(1) // 重置到第一页
  }, [])

  /**
   * 清除筛选条件
   */
  const clearFilters = useCallback(() => {
    setFilters({})
    setCurrentPage(1)
  }, [])

  /**
   * 添加选中的视频
   */
  const addSelectedVideo = useCallback((videoId: string) => {
    setSelectedVideos(prev => {
      if (prev.includes(videoId)) {
        return prev
      }
      return [...prev, videoId]
    })
  }, [])

  /**
   * 移除选中的视频
   */
  const removeSelectedVideo = useCallback((videoId: string) => {
    setSelectedVideos(prev => prev.filter(id => id !== videoId))
  }, [])

  /**
   * 清除所有选中的视频
   */
  const clearSelectedVideos = useCallback(() => {
    setSelectedVideos([])
  }, [])

  const value: VideoContextType = {
    videos,
    loading,
    currentPage,
    total,
    pageSize,
    filters,
    selectedVideos,
    loadVideos,
    refreshVideos,
    deleteVideo,
    getVideo,
    setCurrentPage,
    setPageSize,
    updateFilters,
    clearFilters,
    setSelectedVideos,
    addSelectedVideo,
    removeSelectedVideo,
    clearSelectedVideos,
  }

  return <VideoContext.Provider value={value}>{children}</VideoContext.Provider>
}

/**
 * 使用视频 Context 的 Hook
 */
export const useVideoContext = (): VideoContextType => {
  const context = useContext(VideoContext)
  if (context === undefined) {
    throw new Error('useVideoContext must be used within a VideoProvider')
  }
  return context
}
