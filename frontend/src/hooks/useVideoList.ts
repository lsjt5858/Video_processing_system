import { useState, useEffect } from 'react'
import { message } from 'antd'
import { getVideos, deleteVideo as deleteVideoApi } from '@/services/api'
import type { Video } from '@/types'

interface UseVideoListOptions {
  autoLoad?: boolean
  pageSize?: number
}

interface UseVideoListFilters {
  search?: string
  format?: string
  startDate?: string
  endDate?: string
}

/**
 * 视频列表 Hook
 * 管理视频列表的加载、分页、筛选和操作
 */
export const useVideoList = (options: UseVideoListOptions = {}) => {
  const { autoLoad = true, pageSize = 20 } = options

  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<UseVideoListFilters>({})

  useEffect(() => {
    if (autoLoad) {
      loadVideos()
    }
  }, [currentPage, pageSize, filters])

  /**
   * 加载视频列表
   */
  const loadVideos = async () => {
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
  }

  /**
   * 删除视频
   */
  const deleteVideo = async (videoId: string) => {
    try {
      await deleteVideoApi(videoId)
      message.success('删除成功')
      // 如果当前页只有一个视频且不是第一页，则返回上一页
      if (videos.length === 1 && currentPage > 1) {
        setCurrentPage(currentPage - 1)
      } else {
        loadVideos()
      }
    } catch (error) {
      console.error('Failed to delete video:', error)
      message.error('删除失败')
    }
  }

  /**
   * 刷新视频列表
   */
  const refreshVideos = () => {
    loadVideos()
  }

  /**
   * 更新筛选条件
   */
  const updateFilters = (newFilters: Partial<UseVideoListFilters>) => {
    setFilters({ ...filters, ...newFilters })
    setCurrentPage(1) // 重置到第一页
  }

  /**
   * 清除筛选条件
   */
  const clearFilters = () => {
    setFilters({})
    setCurrentPage(1)
  }

  return {
    videos,
    loading,
    currentPage,
    total,
    pageSize,
    filters,
    setCurrentPage,
    loadVideos,
    deleteVideo,
    refreshVideos,
    updateFilters,
    clearFilters,
  }
}
