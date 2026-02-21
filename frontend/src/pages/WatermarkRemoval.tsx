import { useState, useEffect } from 'react'
import { 
  Card, 
  Radio, 
  Button, 
  Space, 
  Form, 
  Upload, 
  message, 
  Alert, 
  Descriptions, 
  Tag, 
  Slider, 
  InputNumber, 
  Row, 
  Col,
  Spin,
  Divider
} from 'antd'
import { UploadOutlined, DownloadOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import VideoPlayer from '@/components/VideoPlayer'
import ProgressBar from '@/components/ProgressBar'
import { useTaskProgress } from '@/hooks/useTaskProgress'
import { getVideoById, getWatermarks, removeWatermark, downloadProcessedVideo } from '@/services/api'
import type { Video, WatermarkRegion, ProcessingMode } from '@/types'

/**
 * 水印去除页面
 * 提供三种去除模式：裁剪重构、AI修复填充、局部模糊替换
 */
const WatermarkRemoval: React.FC = () => {
  const { videoId } = useParams<{ videoId: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  
  // 视频和水印数据
  const [video, setVideo] = useState<Video | null>(null)
  const [regions, setRegions] = useState<WatermarkRegion[]>([])
  const [loading, setLoading] = useState(true)
  
  // 处理模式和参数
  const [mode, setMode] = useState<ProcessingMode>('crop_reconstruct')
  const [blurMode, setBlurMode] = useState<'blur' | 'logo'>('blur')
  const [customLogo, setCustomLogo] = useState<File | null>(null)
  
  // 裁剪参数
  const [cropParams, setCropParams] = useState({
    x: 0,
    y: 0,
    width: 100,
    height: 100,
    contentIntegrity: 90
  })
  
  // 处理状态
  const [processing, setProcessing] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const { task, progress } = useTaskProgress(taskId || undefined)
  const [resultVideoUrl, setResultVideoUrl] = useState<string>('')

  const isValidVideo = (data: any): data is Video => {
    return (
      data &&
      typeof data === 'object' &&
      typeof data.format === 'string' &&
      data.resolution &&
      typeof data.resolution.width === 'number' &&
      typeof data.resolution.height === 'number' &&
      typeof data.duration === 'number'
    )
  }

  useEffect(() => {
    if (videoId) {
      loadVideoAndWatermarks()
    }
  }, [videoId])

  // 监听任务完成
  useEffect(() => {
    if (task?.status === 'completed') {
      setProcessing(false)
      if (task.result?.output_video_id) {
        setResultVideoUrl(downloadProcessedVideo(task.result.output_video_id))
        message.success('水印去除完成！')
      }
    } else if (task?.status === 'failed') {
      setProcessing(false)
      message.error(`处理失败: ${task.error_message || '未知错误'}`)
    }
  }, [task])

  const loadVideoAndWatermarks = async () => {
    if (!videoId) return
    
    setLoading(true)
    try {
      // 并行加载视频信息和水印区域
      const [videoData, watermarksData] = await Promise.all([
        getVideoById(videoId),
        getWatermarks(videoId)
      ])

      const normalizedVideo = isValidVideo(videoData) ? videoData : null
      setVideo(normalizedVideo)
      setRegions(Array.isArray(watermarksData) ? watermarksData : [])

      // 根据水印区域计算推荐的裁剪参数
      if (normalizedVideo && Array.isArray(watermarksData) && watermarksData.length > 0) {
        calculateOptimalCrop(normalizedVideo, watermarksData)
      }
    } catch (error) {
      message.error('加载视频信息失败')
      console.error('Load error:', error)
    } finally {
      setLoading(false)
    }
  }

  /**
   * 计算最优裁剪区域
   * 分析水印位置，推荐能排除水印且保持主体内容的裁剪参数
   */
  const calculateOptimalCrop = (videoData: Video, watermarkRegions: WatermarkRegion[]) => {
    const videoWidth = videoData.resolution.width
    const videoHeight = videoData.resolution.height
    
    // 找出所有水印的边界
    let minX = videoWidth
    let minY = videoHeight
    let maxX = 0
    let maxY = 0
    
    watermarkRegions.forEach(region => {
      const { bbox } = region
      minX = Math.min(minX, bbox.x)
      minY = Math.min(minY, bbox.y)
      maxX = Math.max(maxX, bbox.x + bbox.width)
      maxY = Math.max(maxY, bbox.y + bbox.height)
    })
    
    // 计算裁剪区域（排除水印）
    // 简单策略：如果水印在边缘，裁剪掉该边缘
    let cropX = 0
    let cropY = 0
    let cropWidth = videoWidth
    let cropHeight = videoHeight
    
    // 如果水印在左边缘
    if (minX < videoWidth * 0.1) {
      cropX = maxX
      cropWidth = videoWidth - maxX
    }
    // 如果水印在右边缘
    else if (maxX > videoWidth * 0.9) {
      cropWidth = minX
    }
    
    // 如果水印在顶部
    if (minY < videoHeight * 0.1) {
      cropY = maxY
      cropHeight = videoHeight - maxY
    }
    // 如果水印在底部
    else if (maxY > videoHeight * 0.9) {
      cropHeight = minY
    }
    
    // 计算内容完整度
    const contentIntegrity = Math.round((cropWidth * cropHeight) / (videoWidth * videoHeight) * 100)
    
    setCropParams({
      x: cropX,
      y: cropY,
      width: cropWidth,
      height: cropHeight,
      contentIntegrity
    })
  }

  const handleProcess = async () => {
    if (!videoId || regions.length === 0) {
      message.warning('请先标记水印区域')
      return
    }

    setProcessing(true)

    try {
      // 准备处理参数
      const params: any = {
        mode,
        regions: regions.map(r => ({
          region_id: r.region_id,
          bbox: r.bbox,
          start_time: r.start_time,
          end_time: r.end_time
        }))
      }
      
      // 根据模式添加特定参数
      if (mode === 'crop_reconstruct') {
        params.crop_params = cropParams
      } else if (mode === 'blur_replace') {
        params.blur_mode = blurMode
        if (blurMode === 'logo' && customLogo) {
          // TODO: 上传logo文件并获取路径
          params.custom_logo = 'path/to/logo'
        }
      }
      
      // 调用API开始处理
      const response = await removeWatermark(videoId, params)
      
      // 保存任务ID用于进度跟踪
      setTaskId(response.task_id)
      message.success('任务已提交，正在处理...')
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || '提交任务失败')
      setProcessing(false)
      console.error('Process error:', error)
    }
  }

  const handleDownload = () => {
    if (resultVideoUrl) {
      window.open(resultVideoUrl, '_blank')
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  }

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载视频信息..." />
      </div>
    )
  }

  if (!video) {
    return (
      <Card title="水印去除">
        <Alert
          message="视频不存在"
          description="未找到指定的视频，请返回视频列表"
          type="error"
          showIcon
          action={
            <Button onClick={() => navigate('/videos')}>
              返回列表
            </Button>
          }
        />
      </Card>
    )
  }

  return (
    <div>
      <Card 
        title={
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate(`/watermark-marker/${videoId}`)}
            >
              返回标记
            </Button>
            <span>水印去除</span>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 视频信息 */}
          <Card title="视频信息" size="small">
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="分辨率">
                {video.resolution.width} × {video.resolution.height}
              </Descriptions.Item>
              <Descriptions.Item label="时长">
                {formatDuration(video.duration)}
              </Descriptions.Item>
              <Descriptions.Item label="格式">
                {video.format.toUpperCase()}
              </Descriptions.Item>
              <Descriptions.Item label="编码">
                {video.codec}
              </Descriptions.Item>
              <Descriptions.Item label="帧率">
                {video.framerate} fps
              </Descriptions.Item>
              <Descriptions.Item label="码率">
                {Math.round(video.bitrate / 1000)} kbps
              </Descriptions.Item>
              <Descriptions.Item label="文件大小">
                {formatFileSize(video.file_size)}
              </Descriptions.Item>
              <Descriptions.Item label="水印区域">
                <Tag color="blue">{regions.length} 个</Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* 水印区域信息 */}
          {regions.length > 0 && (
            <Card title="水印区域" size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                {regions.map((region) => (
                  <Card key={region.region_id} size="small" type="inner">
                    <Descriptions column={2} size="small">
                      <Descriptions.Item label={`区域 #${region.region_id.slice(-4)}`}>
                        <Tag color={region.detection_method === 'auto' ? 'green' : 'blue'}>
                          {region.detection_method === 'auto' ? '自动检测' : '手动标记'}
                        </Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="类型">
                        {region.watermark_type}
                      </Descriptions.Item>
                      <Descriptions.Item label="位置">
                        ({region.bbox.x}, {region.bbox.y})
                      </Descriptions.Item>
                      <Descriptions.Item label="大小">
                        {region.bbox.width} × {region.bbox.height}
                      </Descriptions.Item>
                      <Descriptions.Item label="时间范围">
                        {region.start_time.toFixed(1)}s - {region.end_time.toFixed(1)}s
                      </Descriptions.Item>
                      {region.detection_method === 'auto' && (
                        <Descriptions.Item label="置信度">
                          {(region.confidence * 100).toFixed(1)}%
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  </Card>
                ))}
              </Space>
            </Card>
          )}

          {/* 原始视频预览 */}
          <Card title="原始视频预览" size="small">
            <VideoPlayer videoUrl={video.storage_path} />
          </Card>

          <Divider />

          {/* 处理模式选择和参数设置 */}
          <Form
            form={form}
            layout="vertical"
            onFinish={handleProcess}
          >
            <Card title="去除模式选择" size="small">
              <Form.Item label="选择去除模式">
                <Radio.Group 
                  value={mode} 
                  onChange={(e) => setMode(e.target.value)}
                  disabled={processing}
                >
                  <Space direction="vertical">
                    <Radio value="crop_reconstruct">
                      <strong>裁剪重构模式（推荐）</strong>
                      <div style={{ color: '#666', fontSize: '12px' }}>
                        智能裁剪视频，排除水印区域，保持主体内容完整度≥90%
                      </div>
                    </Radio>
                    <Radio value="ai_inpainting">
                      <strong>AI修复填充模式</strong>
                      <div style={{ color: '#666', fontSize: '12px' }}>
                        使用AI算法修复水印区域，保持视频尺寸不变（处理时间较长）
                      </div>
                    </Radio>
                    <Radio value="blur_replace">
                      <strong>局部模糊替换模式</strong>
                      <div style={{ color: '#666', fontSize: '12px' }}>
                        对水印区域进行模糊处理或替换为自定义logo（快速处理）
                      </div>
                    </Radio>
                  </Space>
                </Radio.Group>
              </Form.Item>
            </Card>

            {/* 裁剪模式参数 */}
            {mode === 'crop_reconstruct' && (
              <Card title="裁剪参数设置" size="small">
                <Alert
                  message="裁剪预览"
                  description={`推荐裁剪区域：从 (${cropParams.x}, ${cropParams.y}) 开始，大小 ${cropParams.width} × ${cropParams.height}，内容完整度：${cropParams.contentIntegrity}%`}
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="裁剪起始 X">
                      <InputNumber
                        min={0}
                        max={video.resolution.width}
                        value={cropParams.x}
                        onChange={(value) => setCropParams({ ...cropParams, x: value || 0 })}
                        style={{ width: '100%' }}
                        disabled={processing}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="裁剪起始 Y">
                      <InputNumber
                        min={0}
                        max={video.resolution.height}
                        value={cropParams.y}
                        onChange={(value) => setCropParams({ ...cropParams, y: value || 0 })}
                        style={{ width: '100%' }}
                        disabled={processing}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="裁剪宽度">
                      <Slider
                        min={1}
                        max={video.resolution.width}
                        value={cropParams.width}
                        onChange={(value) => setCropParams({ ...cropParams, width: value })}
                        disabled={processing}
                      />
                      <InputNumber
                        min={1}
                        max={video.resolution.width}
                        value={cropParams.width}
                        onChange={(value) => setCropParams({ ...cropParams, width: value || 1 })}
                        style={{ width: '100%' }}
                        disabled={processing}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="裁剪高度">
                      <Slider
                        min={1}
                        max={video.resolution.height}
                        value={cropParams.height}
                        onChange={(value) => setCropParams({ ...cropParams, height: value })}
                        disabled={processing}
                      />
                      <InputNumber
                        min={1}
                        max={video.resolution.height}
                        value={cropParams.height}
                        onChange={(value) => setCropParams({ ...cropParams, height: value || 1 })}
                        style={{ width: '100%' }}
                        disabled={processing}
                      />
                    </Form.Item>
                  </Col>
                </Row>
                
                <Alert
                  message={
                    cropParams.contentIntegrity >= 90 
                      ? '内容完整度良好' 
                      : '警告：内容完整度低于90%'
                  }
                  description={`当前内容完整度：${cropParams.contentIntegrity}%`}
                  type={cropParams.contentIntegrity >= 90 ? 'success' : 'warning'}
                  showIcon
                />
              </Card>
            )}

            {/* 模糊替换模式参数 */}
            {mode === 'blur_replace' && (
              <Card title="替换参数设置" size="small">
                <Form.Item label="替换方式">
                  <Radio.Group 
                    value={blurMode} 
                    onChange={(e) => setBlurMode(e.target.value)}
                    disabled={processing}
                  >
                    <Radio value="blur">高斯模糊</Radio>
                    <Radio value="logo">自定义Logo</Radio>
                  </Radio.Group>
                </Form.Item>

                {blurMode === 'logo' && (
                  <Form.Item label="上传Logo图片">
                    <Upload
                      beforeUpload={(file) => {
                        setCustomLogo(file)
                        return false
                      }}
                      maxCount={1}
                      accept="image/*"
                      disabled={processing}
                    >
                      <Button icon={<UploadOutlined />}>选择Logo图片</Button>
                    </Upload>
                    {customLogo && (
                      <div style={{ marginTop: 8 }}>
                        已选择: {customLogo.name}
                      </div>
                    )}
                  </Form.Item>
                )}
              </Card>
            )}

            {/* 处理进度 */}
            {processing && (
              <Card title="处理进度" size="small">
                <ProgressBar 
                  percent={progress} 
                  status={task?.status === 'failed' ? 'exception' : progress === 100 ? 'success' : 'active'}
                />
                <div style={{ marginTop: 8, textAlign: 'center', color: '#666' }}>
                  {task?.status === 'pending' && '等待处理...'}
                  {task?.status === 'processing' && `正在处理... ${progress}%`}
                  {task?.status === 'completed' && '处理完成！'}
                  {task?.status === 'failed' && `处理失败: ${task.error_message}`}
                </div>
              </Card>
            )}

            {/* 处理完成提示 */}
            {task?.status === 'completed' && resultVideoUrl && (
              <Alert
                message="处理完成"
                description="视频已成功处理，您可以预览或下载处理后的视频"
                type="success"
                showIcon
              />
            )}

            {/* 操作按钮 */}
            <Form.Item>
              <Space>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={processing}
                  disabled={regions.length === 0 || processing}
                  size="large"
                >
                  {processing ? '处理中...' : '开始处理'}
                </Button>
                <Button 
                  onClick={() => navigate(`/watermark-marker/${videoId}`)}
                  disabled={processing}
                  size="large"
                >
                  返回标记
                </Button>
                {resultVideoUrl && (
                  <>
                    <Button 
                      type="primary"
                      icon={<DownloadOutlined />}
                      onClick={handleDownload}
                      size="large"
                    >
                      下载视频
                    </Button>
                    <Button onClick={() => navigate('/task-manager')} size="large">
                      查看任务管理
                    </Button>
                  </>
                )}
              </Space>
            </Form.Item>
          </Form>

          {/* 处理结果预览 */}
          {resultVideoUrl && (
            <Card title="处理结果预览" size="small">
              <VideoPlayer videoUrl={resultVideoUrl} />
            </Card>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default WatermarkRemoval
