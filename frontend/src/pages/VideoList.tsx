import { useState } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  message, 
  Modal, 
  Input, 
  Select, 
  DatePicker,
  Empty,
  Skeleton
} from 'antd'
import { 
  PlusOutlined, 
  EyeOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  EditOutlined,
  ScissorOutlined,
  ClearOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { Video, VideoFormat } from '@/types'
import { useVideoList } from '@/hooks/useVideoList'
import VideoThumbnail from '@/components/VideoThumbnail'
import type { ColumnsType } from 'antd/es/table'
import dayjs, { Dayjs } from 'dayjs'

const { Search } = Input
const { RangePicker } = DatePicker

/**
 * 视频列表页面
 * 显示用户上传的所有视频，支持分页、搜索、筛选、删除等操作
 */
const VideoList: React.FC = () => {
  const navigate = useNavigate()
  
  // 搜索和筛选状态
  const [searchText, setSearchText] = useState('')
  const [formatFilter, setFormatFilter] = useState<VideoFormat | undefined>()
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)
  
  // 使用自定义 Hook 管理视频列表
  const {
    videos,
    loading,
    currentPage,
    total,
    pageSize,
    setCurrentPage,
    deleteVideo,
    refreshVideos,
  } = useVideoList({ autoLoad: true, pageSize: 20 })

  /**
   * 格式化时长（秒转 HH:MM:SS）
   */
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  /**
   * 格式化文件大小（字节转 MB/GB）
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(2)} KB`
    } else if (bytes < 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
    } else {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
    }
  }

  /**
   * 格式化日期时间
   */
  const formatDateTime = (dateStr: string): string => {
    return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
  }

  /**
   * 处理删除操作
   */
  const handleDelete = (videoId: string, filename: string) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除视频 "${filename}" 吗？此操作不可恢复。`,
      okText: '确认',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        await deleteVideo(videoId)
      },
    })
  }

  /**
   * 清除所有筛选条件
   */
  const handleClearFilters = () => {
    setSearchText('')
    setFormatFilter(undefined)
    setDateRange(null)
    message.success('已清除所有筛选条件')
  }

  /**
   * 应用筛选（客户端筛选）
   */
  const getFilteredVideos = () => {
    let filtered = [...videos]

    // 按文件名搜索
    if (searchText) {
      filtered = filtered.filter(video => 
        video.storage_path.toLowerCase().includes(searchText.toLowerCase()) ||
        video.video_id.toLowerCase().includes(searchText.toLowerCase())
      )
    }

    // 按格式筛选
    if (formatFilter) {
      filtered = filtered.filter(video => video.format === formatFilter)
    }

    // 按日期范围筛选
    if (dateRange) {
      const [start, end] = dateRange
      filtered = filtered.filter(video => {
        const videoDate = dayjs(video.created_at)
        return videoDate.isAfter(start) && videoDate.isBefore(end)
      })
    }

    return filtered
  }

  /**
   * 表格列定义
   */
  const columns: ColumnsType<Video> = [
    {
      title: '缩略图',
      key: 'thumbnail',
      width: 120,
      render: (_, record) => (
        <VideoThumbnail
          videoId={record.video_id}
          thumbnailUrl={`/api/videos/${record.video_id}/thumbnail`}
          duration={record.duration}
          onClick={() => navigate(`/watermark-marker/${record.video_id}`)}
        />
      ),
    },
    {
      title: '文件名',
      key: 'filename',
      width: 200,
      ellipsis: true,
      render: (_, record) => {
        const filename = record.storage_path.split('/').pop() || record.video_id
        return <span title={filename}>{filename}</span>
      },
    },
    {
      title: '分辨率',
      key: 'resolution',
      width: 120,
      render: (_, record) => 
        `${record.resolution.width}×${record.resolution.height}`,
    },
    {
      title: '时长',
      key: 'duration',
      width: 100,
      render: (_, record) => formatDuration(record.duration),
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      width: 80,
      render: (format: string) => <Tag color="blue">{format.toUpperCase()}</Tag>,
    },
    {
      title: '文件大小',
      key: 'file_size',
      width: 100,
      render: (_, record) => formatFileSize(record.file_size),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => formatDateTime(date),
      sorter: (a, b) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/watermark-marker/${record.video_id}`)}
          >
            查看详情
          </Button>
          <Button 
            type="link" 
            size="small"
            icon={<EditOutlined />}
            onClick={() => navigate(`/watermark-marker/${record.video_id}`)}
          >
            标记水印
          </Button>
          <Button 
            type="link" 
            size="small"
            icon={<ScissorOutlined />}
            onClick={() => navigate(`/watermark-removal/${record.video_id}`)}
          >
            去除水印
          </Button>
          <Button 
            type="link" 
            size="small"
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.video_id, record.storage_path.split('/').pop() || record.video_id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  const filteredVideos = getFilteredVideos()

  return (
    <div style={{ padding: '24px' }}>
      <Card 
        title={
          <Space>
            <span>视频列表</span>
            <Tag color="blue">{total} 个视频</Tag>
          </Space>
        }
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              onClick={refreshVideos}
              loading={loading}
            >
              刷新
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => navigate('/upload')}
            >
              上传视频
            </Button>
          </Space>
        }
      >
        {/* 搜索和筛选区域 */}
        <Space direction="vertical" size="middle" style={{ width: '100%', marginBottom: 16 }}>
          <Space wrap>
            <Search
              placeholder="搜索文件名或视频ID"
              allowClear
              style={{ width: 300 }}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={(value) => setSearchText(value)}
            />
            <Select
              placeholder="选择格式"
              allowClear
              style={{ width: 150 }}
              value={formatFilter}
              onChange={(value) => setFormatFilter(value)}
              options={[
                { label: 'MP4', value: 'mp4' },
                { label: 'AVI', value: 'avi' },
                { label: 'MOV', value: 'mov' },
                { label: 'MKV', value: 'mkv' },
              ]}
            />
            <RangePicker
              placeholder={['开始日期', '结束日期']}
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs] | null)}
            />
            <Button 
              icon={<ClearOutlined />}
              onClick={handleClearFilters}
            >
              清除筛选
            </Button>
          </Space>
        </Space>

        {/* 视频列表表格 */}
        {loading ? (
          <Skeleton active paragraph={{ rows: 5 }} />
        ) : filteredVideos.length === 0 ? (
          <Empty
            description={videos.length === 0 ? "暂无视频，请先上传视频" : "没有符合条件的视频"}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            {videos.length === 0 && (
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => navigate('/upload')}
              >
                立即上传
              </Button>
            )}
          </Empty>
        ) : (
          <Table
            columns={columns}
            dataSource={filteredVideos}
            loading={loading}
            rowKey="video_id"
            scroll={{ x: 1200 }}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 个视频`,
              pageSizeOptions: ['10', '20', '50', '100'],
              onChange: (page) => {
                setCurrentPage(page)
              },
            }}
          />
        )}
      </Card>
    </div>
  )
}

export default VideoList
