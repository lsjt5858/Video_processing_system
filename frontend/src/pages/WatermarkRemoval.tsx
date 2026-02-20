import { useState, useEffect } from 'react'
import { Card, Radio, Button, Space, Form, Upload, message, Alert } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import VideoPlayer from '@/components/VideoPlayer'
import ProgressBar from '@/components/ProgressBar'
import type { Video, WatermarkRegion, ProcessingMode } from '@/types'

/**
 * 水印去除页面
 * 提供三种去除模式：裁剪重构、AI修复填充、局部模糊替换
 */
const WatermarkRemoval: React.FC = () => {
  const { videoId } = useParams<{ videoId: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [video] = useState<Video | null>(null)
  const [regions] = useState<WatermarkRegion[]>([])
  const [mode, setMode] = useState<ProcessingMode>('crop_reconstruct')
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [resultVideoUrl] = useState<string>('')

  useEffect(() => {
    if (videoId) {
      loadVideo()
      loadWatermarks()
    }
  }, [videoId])

  const loadVideo = async () => {
    try {
      // TODO: 调用API获取视频信息
      message.info('视频加载功能待实现')
    } catch (error) {
      message.error('加载视频失败')
    }
  }

  const loadWatermarks = async () => {
    try {
      // TODO: 调用API获取水印区域
    } catch (error) {
      message.error('加载水印信息失败')
    }
  }

  const handleProcess = async (_values: any) => {
    setProcessing(true)
    setProgress(0)

    try {
      // TODO: 调用API处理视频
      // const response = await api.post(`/videos/${videoId}/remove`, {
      //   mode,
      //   regions,
      //   ...values
      // })
      
      // 模拟进度更新
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval)
            return 100
          }
          return prev + 10
        })
      }, 500)

      message.success('水印去除功能待实现')
    } catch (error) {
      message.error('处理失败')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div>
      <Card title="水印去除">
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 原始视频预览 */}
          <Card title="原始视频" size="small">
            <VideoPlayer videoUrl={video?.storage_path || ''} />
          </Card>

          {/* 处理模式选择 */}
          <Form
            form={form}
            layout="vertical"
            onFinish={handleProcess}
          >
            <Form.Item label="选择去除模式">
              <Radio.Group 
                value={mode} 
                onChange={(e) => setMode(e.target.value)}
              >
                <Space direction="vertical">
                  <Radio value="crop_reconstruct">
                    <strong>裁剪重构</strong>
                    <div style={{ color: '#666', fontSize: '12px' }}>
                      智能裁剪视频，排除水印区域，保持主体内容完整
                    </div>
                  </Radio>
                  <Radio value="ai_inpainting">
                    <strong>AI修复填充</strong>
                    <div style={{ color: '#666', fontSize: '12px' }}>
                      使用AI算法修复水印区域，保持视频尺寸不变
                    </div>
                  </Radio>
                  <Radio value="blur_replace">
                    <strong>局部模糊替换</strong>
                    <div style={{ color: '#666', fontSize: '12px' }}>
                      对水印区域进行模糊处理或替换为自定义logo
                    </div>
                  </Radio>
                </Space>
              </Radio.Group>
            </Form.Item>

            {mode === 'blur_replace' && (
              <Form.Item label="替换选项">
                <Radio.Group defaultValue="blur">
                  <Radio value="blur">高斯模糊</Radio>
                  <Radio value="logo">自定义Logo</Radio>
                </Radio.Group>
              </Form.Item>
            )}

            {mode === 'blur_replace' && (
              <Form.Item label="上传Logo">
                <Upload beforeUpload={() => false}>
                  <Button icon={<UploadOutlined />}>选择Logo图片</Button>
                </Upload>
              </Form.Item>
            )}

            {processing && (
              <Form.Item>
                <ProgressBar 
                  percent={progress} 
                  status={progress === 100 ? 'success' : 'active'}
                />
              </Form.Item>
            )}

            {progress === 100 && resultVideoUrl && (
              <Alert
                message="处理完成"
                description="视频已成功处理，请查看结果"
                type="success"
                showIcon
              />
            )}

            <Form.Item>
              <Space>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={processing}
                  disabled={regions.length === 0}
                >
                  开始处理
                </Button>
                <Button onClick={() => navigate(`/watermark-marker/${videoId}`)}>
                  返回标记
                </Button>
                {resultVideoUrl && (
                  <Button type="primary" onClick={() => navigate('/task-manager')}>
                    查看任务
                  </Button>
                )}
              </Space>
            </Form.Item>
          </Form>

          {/* 处理结果预览 */}
          {resultVideoUrl && (
            <Card title="处理结果" size="small">
              <VideoPlayer videoUrl={resultVideoUrl} />
            </Card>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default WatermarkRemoval
