import { useState, useEffect } from 'react'
import { 
  Card, Button, Space, List, Tag, message, Spin, Row, Col, 
  Modal, Form, InputNumber, Select, Divider, Alert, Tooltip 
} from 'antd'
import { 
  PlusOutlined, DeleteOutlined, EditOutlined, SaveOutlined, 
  LeftOutlined, RightOutlined, ZoomInOutlined, ZoomOutOutlined,
  ClearOutlined
} from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import WatermarkCanvas from '@/components/WatermarkCanvas'
import type { Video, WatermarkRegion, BoundingBox } from '@/types'
import { getVideoById, getVideoFrames, getWatermarks, markWatermark, updateWatermark, deleteWatermark } from '@/services/api'

/**
 * 水印标记页面
 * 功能：
 * 1. 显示视频帧
 * 2. 鼠标拖拽绘制矩形框
 * 3. 显示已标记的水印区域列表
 * 4. 支持编辑、删除水印区域
 * 5. 提供批量标记模式（切换不同视频）
 * 6. 帧导航（上一帧/下一帧）
 * 7. 画布缩放功能
 */
const WatermarkMarker: React.FC = () => {
  const { videoId } = useParams<{ videoId: string }>()
  const navigate = useNavigate()
  
  // 视频和帧相关状态
  const [video, setVideo] = useState<Video | null>(null)
  const [frames, setFrames] = useState<string[]>([])
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [framesLoading, setFramesLoading] = useState(false)
  
  // 水印区域相关状态
  const [regions, setRegions] = useState<WatermarkRegion[]>([])
  const [markingMode, setMarkingMode] = useState(false)
  const [saving, setSaving] = useState(false)
  
  // 编辑模式相关状态
  const [editingRegion, setEditingRegion] = useState<WatermarkRegion | null>(null)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [form] = Form.useForm()
  
  // 画布缩放
  const [zoomLevel, setZoomLevel] = useState(1)

  useEffect(() => {
    if (videoId) {
      loadVideo()
      loadFrames()
      loadWatermarks()
    }
  }, [videoId])

  /**
   * 加载视频信息
   */
  const loadVideo = async () => {
    setLoading(true)
    try {
      const videoData = await getVideoById(videoId!)
      setVideo(videoData)
    } catch (error) {
      message.error('加载视频失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  /**
   * 加载视频帧
   */
  const loadFrames = async () => {
    setFramesLoading(true)
    try {
      const response = await getVideoFrames(videoId!)
      setFrames(response.frames || [])
      if (response.frames && response.frames.length > 0) {
        setCurrentFrameIndex(0)
      }
    } catch (error) {
      message.error('加载视频帧失败')
      console.error(error)
    } finally {
      setFramesLoading(false)
    }
  }

  /**
   * 加载已标记的水印区域
   */
  const loadWatermarks = async () => {
    try {
      const watermarks = await getWatermarks(videoId!)
      setRegions(watermarks || [])
    } catch (error) {
      console.error('加载水印信息失败:', error)
    }
  }

  /**
   * 手动标记水印区域
   */
  const handleManualMark = (region: WatermarkRegion) => {
    setRegions([...regions, region])
    message.success('水印区域已添加')
  }

  /**
   * 删除水印区域
   */
  const handleDeleteRegion = async (regionId: string) => {
    try {
      await deleteWatermark(videoId!, regionId)
      setRegions(regions.filter(r => r.region_id !== regionId))
      message.success('水印区域已删除')
    } catch (error) {
      message.error('删除失败')
      console.error(error)
    }
  }

  /**
   * 打开编辑对话框
   */
  const handleEditRegion = (region: WatermarkRegion) => {
    setEditingRegion(region)
    form.setFieldsValue({
      x: region.bbox.x,
      y: region.bbox.y,
      width: region.bbox.width,
      height: region.bbox.height,
      watermark_type: region.watermark_type,
    })
    setEditModalVisible(true)
  }

  /**
   * 保存编辑的水印区域
   */
  const handleSaveEdit = async () => {
    try {
      const values = await form.validateFields()
      const updatedBbox: BoundingBox = {
        x: values.x,
        y: values.y,
        width: values.width,
        height: values.height,
      }
      
      await updateWatermark(videoId!, editingRegion!.region_id, updatedBbox)
      
      setRegions(regions.map(r => 
        r.region_id === editingRegion!.region_id 
          ? { ...r, bbox: updatedBbox, watermark_type: values.watermark_type }
          : r
      ))
      
      message.success('水印区域已更新')
      setEditModalVisible(false)
      setEditingRegion(null)
    } catch (error) {
      message.error('更新失败')
      console.error(error)
    }
  }

  /**
   * 保存所有水印区域到后端
   */
  const handleSaveAll = async () => {
    if (regions.length === 0) {
      message.warning('请至少标记一个水印区域')
      return
    }
    
    setSaving(true)
    try {
      await markWatermark(videoId!, regions)
      message.success('水印区域已保存')
    } catch (error) {
      message.error('保存失败')
      console.error(error)
    } finally {
      setSaving(false)
    }
  }

  /**
   * 清空所有水印区域
   */
  const handleClearAll = () => {
    Modal.confirm({
      title: '确认清空',
      content: '确定要清空所有已标记的水印区域吗？',
      onOk: () => {
        setRegions([])
        message.success('已清空所有水印区域')
      },
    })
  }

  /**
   * 帧导航：上一帧
   */
  const handlePreviousFrame = () => {
    if (currentFrameIndex > 0) {
      setCurrentFrameIndex(currentFrameIndex - 1)
    }
  }

  /**
   * 帧导航：下一帧
   */
  const handleNextFrame = () => {
    if (currentFrameIndex < frames.length - 1) {
      setCurrentFrameIndex(currentFrameIndex + 1)
    }
  }

  /**
   * 缩放画布
   */
  const handleZoomIn = () => {
    setZoomLevel(Math.min(zoomLevel + 0.1, 2))
  }

  const handleZoomOut = () => {
    setZoomLevel(Math.max(zoomLevel - 0.1, 0.5))
  }

  /**
   * 下一步：去除水印
   */
  const handleNext = () => {
    if (regions.length === 0) {
      message.warning('请至少标记一个水印区域')
      return
    }
    navigate(`/watermark-removal/${videoId}`)
  }

  /**
   * 获取当前帧的URL
   */
  const getCurrentFrameUrl = () => {
    if (frames.length === 0) return ''
    return frames[currentFrameIndex]
  }

  /**
   * 获取当前帧的时间戳
   */
  const getCurrentFrameTimestamp = () => {
    if (!video || frames.length === 0) return 0
    return (currentFrameIndex / frames.length) * video.duration
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card 
        title={
          <Space>
            <span>水印标记</span>
            {video && (
              <Tag color="blue">
                {video.format.toUpperCase()} | {video.resolution.width}x{video.resolution.height} | {video.duration.toFixed(2)}s
              </Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Button 
              icon={<PlusOutlined />}
              type={markingMode ? 'primary' : 'default'}
              onClick={() => setMarkingMode(!markingMode)}
            >
              {markingMode ? '取消标记' : '手动标记'}
            </Button>
            <Button 
              icon={<SaveOutlined />}
              type="primary"
              loading={saving}
              onClick={handleSaveAll}
              disabled={regions.length === 0}
            >
              保存
            </Button>
            <Button 
              icon={<ClearOutlined />}
              danger
              onClick={handleClearAll}
              disabled={regions.length === 0}
            >
              清空
            </Button>
          </Space>
        }
      >
        <Row gutter={24}>
          {/* 左侧：视频帧和画布 */}
          <Col span={16}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* 使用说明 */}
              {markingMode && (
                <Alert
                  message="标记模式已启用"
                  description="在视频帧上按住鼠标左键拖拽即可绘制矩形框标记水印区域"
                  type="info"
                  showIcon
                  closable
                />
              )}

              {/* 帧导航和缩放控制 */}
              <Card size="small">
                <Space split={<Divider type="vertical" />}>
                  <Space>
                    <Tooltip title="上一帧">
                      <Button 
                        icon={<LeftOutlined />}
                        onClick={handlePreviousFrame}
                        disabled={currentFrameIndex === 0 || framesLoading}
                      />
                    </Tooltip>
                    <span>
                      帧 {currentFrameIndex + 1} / {frames.length}
                      {video && ` (${getCurrentFrameTimestamp().toFixed(2)}s)`}
                    </span>
                    <Tooltip title="下一帧">
                      <Button 
                        icon={<RightOutlined />}
                        onClick={handleNextFrame}
                        disabled={currentFrameIndex === frames.length - 1 || framesLoading}
                      />
                    </Tooltip>
                  </Space>
                  
                  <Space>
                    <Tooltip title="放大">
                      <Button 
                        icon={<ZoomInOutlined />}
                        onClick={handleZoomIn}
                        disabled={zoomLevel >= 2}
                      />
                    </Tooltip>
                    <span>缩放: {(zoomLevel * 100).toFixed(0)}%</span>
                    <Tooltip title="缩小">
                      <Button 
                        icon={<ZoomOutOutlined />}
                        onClick={handleZoomOut}
                        disabled={zoomLevel <= 0.5}
                      />
                    </Tooltip>
                  </Space>
                </Space>
              </Card>

              {/* 视频帧和标记画布 */}
              <div style={{ 
                position: 'relative', 
                border: '1px solid #d9d9d9',
                borderRadius: '4px',
                overflow: 'auto',
                maxHeight: '600px',
              }}>
                {framesLoading ? (
                  <div style={{ textAlign: 'center', padding: '100px 0' }}>
                    <Spin tip="加载视频帧中..." />
                  </div>
                ) : frames.length > 0 ? (
                  <div style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}>
                    <WatermarkCanvas 
                      videoId={videoId!}
                      frameUrl={getCurrentFrameUrl()}
                      currentTime={getCurrentFrameTimestamp()}
                      videoDuration={video?.duration || 0}
                      onRegionMarked={handleManualMark}
                      markingMode={markingMode}
                      existingRegions={regions}
                    />
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '100px 0' }}>
                    <p>暂无视频帧</p>
                  </div>
                )}
              </div>
            </Space>
          </Col>

          {/* 右侧：水印区域列表 */}
          <Col span={8}>
            <Card 
              title={`已标记的水印区域 (${regions.length})`}
              size="small"
              style={{ height: '100%' }}
            >
              <List
                dataSource={regions}
                locale={{ emptyText: '暂无标记的水印区域' }}
                renderItem={(region, index) => (
                  <List.Item
                    actions={[
                      <Tooltip title="编辑">
                        <Button 
                          type="link" 
                          icon={<EditOutlined />}
                          size="small"
                          onClick={() => handleEditRegion(region)}
                        />
                      </Tooltip>,
                      <Tooltip title="删除">
                        <Button 
                          type="link" 
                          danger 
                          icon={<DeleteOutlined />}
                          size="small"
                          onClick={() => handleDeleteRegion(region.region_id)}
                        />
                      </Tooltip>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <span>区域 {index + 1}</span>
                          <Tag color={region.detection_method === 'auto' ? 'blue' : 'green'}>
                            {region.detection_method === 'auto' ? '自动' : '手动'}
                          </Tag>
                        </Space>
                      }
                      description={
                        <div style={{ fontSize: '12px' }}>
                          <div>位置: ({region.bbox.x}, {region.bbox.y})</div>
                          <div>大小: {region.bbox.width} × {region.bbox.height}</div>
                          <div>类型: {region.watermark_type}</div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>

        {/* 底部操作按钮 */}
        <Divider />
        <Space>
          <Button type="primary" onClick={handleNext} disabled={regions.length === 0}>
            下一步：去除水印
          </Button>
          <Button onClick={() => navigate('/videos')}>
            返回列表
          </Button>
        </Space>
      </Card>

      {/* 编辑水印区域对话框 */}
      <Modal
        title="编辑水印区域"
        open={editModalVisible}
        onOk={handleSaveEdit}
        onCancel={() => {
          setEditModalVisible(false)
          setEditingRegion(null)
        }}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="X 坐标"
                name="x"
                rules={[{ required: true, message: '请输入X坐标' }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Y 坐标"
                name="y"
                rules={[{ required: true, message: '请输入Y坐标' }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="宽度"
                name="width"
                rules={[{ required: true, message: '请输入宽度' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="高度"
                name="height"
                rules={[{ required: true, message: '请输入高度' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            label="水印类型"
            name="watermark_type"
            rules={[{ required: true, message: '请选择水印类型' }]}
          >
            <Select>
              <Select.Option value="corner">角标</Select.Option>
              <Select.Option value="rolling">滚动</Select.Option>
              <Select.Option value="logo">Logo</Select.Option>
              <Select.Option value="subtitle">字幕</Select.Option>
              <Select.Option value="manual">手动标记</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default WatermarkMarker
