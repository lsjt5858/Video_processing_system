import { useState, useEffect } from 'react'
import { Card, Button, Space, List, Tag, message, Spin } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import VideoPlayer from '@/components/VideoPlayer'
import WatermarkCanvas from '@/components/WatermarkCanvas'
import type { Video, WatermarkRegion } from '@/types'

/**
 * 水印标记页面
 * 支持自动检测和手动标记水印区域
 */
const WatermarkMarker: React.FC = () => {
  const { videoId } = useParams<{ videoId: string }>()
  const navigate = useNavigate()
  const [video] = useState<Video | null>(null)
  const [regions, setRegions] = useState<WatermarkRegion[]>([])
  const [loading, setLoading] = useState(false)
  const [detecting, setDetecting] = useState(false)
  const [markingMode, setMarkingMode] = useState(false)

  useEffect(() => {
    if (videoId) {
      loadVideo()
      loadWatermarks()
    }
  }, [videoId])

  const loadVideo = async () => {
    setLoading(true)
    try {
      // TODO: 调用API获取视频信息
      // const response = await api.get(`/videos/${videoId}`)
      // setVideo(response.data)
      message.info('视频加载功能待实现')
    } catch (error) {
      message.error('加载视频失败')
    } finally {
      setLoading(false)
    }
  }

  const loadWatermarks = async () => {
    try {
      // TODO: 调用API获取水印区域
      // const response = await api.get(`/videos/${videoId}/watermarks`)
      // setRegions(response.data)
    } catch (error) {
      message.error('加载水印信息失败')
    }
  }

  const handleAutoDetect = async () => {
    setDetecting(true)
    try {
      // TODO: 调用API自动检测水印
      // const response = await api.post(`/videos/${videoId}/detect`)
      // setRegions(response.data.watermarks)
      message.success('自动检测功能待实现')
    } catch (error) {
      message.error('自动检测失败')
    } finally {
      setDetecting(false)
    }
  }

  const handleManualMark = (region: WatermarkRegion) => {
    setRegions([...regions, region])
    message.success('水印区域已添加')
  }

  const handleDeleteRegion = (regionId: string) => {
    setRegions(regions.filter(r => r.region_id !== regionId))
    message.success('水印区域已删除')
  }

  const handleNext = () => {
    if (regions.length === 0) {
      message.warning('请至少标记一个水印区域')
      return
    }
    navigate(`/watermark-removal/${videoId}`)
  }

  if (loading) {
    return <Spin size="large" />
  }

  return (
    <div>
      <Card 
        title="水印标记" 
        extra={
          <Space>
            <Button 
              type="primary" 
              loading={detecting}
              onClick={handleAutoDetect}
            >
              自动检测
            </Button>
            <Button 
              icon={<PlusOutlined />}
              onClick={() => setMarkingMode(!markingMode)}
            >
              {markingMode ? '取消标记' : '手动标记'}
            </Button>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 视频播放器和标记画布 */}
          <div style={{ position: 'relative' }}>
            <VideoPlayer videoUrl={video?.storage_path || ''} />
            {markingMode && (
              <WatermarkCanvas 
                videoId={videoId!}
                onRegionMarked={handleManualMark}
              />
            )}
          </div>

          {/* 水印区域列表 */}
          <Card title="已标记的水印区域" size="small">
            <List
              dataSource={regions}
              renderItem={(region) => (
                <List.Item
                  actions={[
                    <Button 
                      type="link" 
                      icon={<EditOutlined />}
                      size="small"
                    >
                      编辑
                    </Button>,
                    <Button 
                      type="link" 
                      danger 
                      icon={<DeleteOutlined />}
                      size="small"
                      onClick={() => handleDeleteRegion(region.region_id)}
                    >
                      删除
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        <span>区域 {region.region_id}</span>
                        <Tag color={region.detection_method === 'auto' ? 'blue' : 'green'}>
                          {region.detection_method === 'auto' ? '自动检测' : '手动标记'}
                        </Tag>
                        <Tag>{region.watermark_type}</Tag>
                      </Space>
                    }
                    description={
                      `位置: (${region.bbox.x}, ${region.bbox.y}) 
                       大小: ${region.bbox.width}x${region.bbox.height} 
                       时间: ${region.start_time.toFixed(2)}s - ${region.end_time.toFixed(2)}s
                       置信度: ${(region.confidence * 100).toFixed(1)}%`
                    }
                  />
                </List.Item>
              )}
            />
          </Card>

          {/* 操作按钮 */}
          <Space>
            <Button type="primary" onClick={handleNext}>
              下一步：去除水印
            </Button>
            <Button onClick={() => navigate('/videos')}>
              返回列表
            </Button>
          </Space>
        </Space>
      </Card>
    </div>
  )
}

export default WatermarkMarker
