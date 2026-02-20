import { useState } from 'react'
import { Card, Upload, Button, Table, Space, Tag, message, Progress, Modal, Form, Select } from 'antd'
import { UploadOutlined, PlayCircleOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { batchUploadVideos, getVideoFrames, batchRemoveWatermark } from '@/services/api'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { Video, BoundingBox } from '@/types'

interface BatchVideo {
  id: string
  video_id?: string
  name: string
  size: number
  status: 'pending' | 'uploading' | 'uploaded' | 'detecting' | 'detected' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
  watermarkRegions?: BoundingBox[]
  outputPath?: string
}

/**
 * 批量处理页面
 * 支持批量上传、检测和导出视频
 */
const BatchProcessing: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [videos, setVideos] = useState<BatchVideo[]>([])
  const [processing, setProcessing] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [batchParamsVisible, setBatchParamsVisible] = useState(false)
  const [form] = Form.useForm()

  // WebSocket连接用于实时更新进度
  useWebSocket('ws://localhost:8000/ws/batch', {
    onMessage: (data) => {
      if (data.type === 'upload_progress') {
        updateVideoStatus(data.video_id, { progress: data.progress, status: 'uploading' })
      } else if (data.type === 'upload_complete') {
        updateVideoStatus(data.video_id, { progress: 100, status: 'uploaded', video_id: data.video_id })
      } else if (data.type === 'detection_progress') {
        updateVideoStatus(data.video_id, { status: 'detecting', progress: data.progress })
      } else if (data.type === 'detection_complete') {
        updateVideoStatus(data.video_id, { status: 'detected', progress: 100 })
      } else if (data.type === 'processing_progress') {
        updateVideoStatus(data.video_id, { status: 'processing', progress: data.progress })
      } else if (data.type === 'processing_complete') {
        updateVideoStatus(data.video_id, { 
          status: 'completed', 
          progress: 100, 
          outputPath: data.output_path 
        })
      } else if (data.type === 'error') {
        updateVideoStatus(data.video_id, { status: 'failed', error: data.message })
      }
    },
    onError: () => {
      console.warn('WebSocket 连接错误，将使用轮询方式')
    },
    reconnect: true,
    maxReconnectAttempts: 3,
  })

  const updateVideoStatus = (videoId: string, updates: Partial<BatchVideo>) => {
    setVideos(prev => prev.map(v => 
      v.video_id === videoId || v.id === videoId ? { ...v, ...updates } : v
    ))
  }

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择视频文件')
      return
    }

    if (fileList.length > 50) {
      message.error('最多支持50个文件')
      return
    }

    // 检查文件大小
    const oversizedFiles = fileList.filter(f => (f.size || 0) > 5 * 1024 * 1024 * 1024)
    if (oversizedFiles.length > 0) {
      message.error(`以下文件超过5GB限制: ${oversizedFiles.map(f => f.name).join(', ')}`)
      return
    }

    setProcessing(true)

    // 转换文件列表为批量视频对象
    const batchVideos: BatchVideo[] = fileList.map((file, index) => ({
      id: `temp_${index}_${Date.now()}`,
      name: file.name,
      size: file.size || 0,
      status: 'pending',
      progress: 0,
    }))

    setVideos(batchVideos)

    try {
      // 批量上传视频
      const files = fileList.map(f => f.originFileObj as File)
      
      // 并行上传最多5个文件
      const chunkSize = 5
      for (let i = 0; i < files.length; i += chunkSize) {
        const chunk = files.slice(i, i + chunkSize)
        const chunkVideos = batchVideos.slice(i, i + chunkSize)
        
        // 更新状态为上传中
        chunkVideos.forEach(v => {
          updateVideoStatus(v.id, { status: 'uploading', progress: 0 })
        })

        try {
          const response = await batchUploadVideos(chunk)
          
          // 更新上传成功的视频
          response.results.forEach((video: Video, idx: number) => {
            const tempVideo = chunkVideos[idx]
            updateVideoStatus(tempVideo.id, {
              video_id: video.video_id,
              status: 'uploaded',
              progress: 100
            })
          })
        } catch (error) {
          // 标记失败的视频
          chunkVideos.forEach(v => {
            updateVideoStatus(v.id, { 
              status: 'failed', 
              error: '上传失败' 
            })
          })
        }
      }

      message.success('批量上传完成')
      setFileList([])
    } catch (error) {
      message.error('批量上传失败')
      console.error(error)
    } finally {
      setProcessing(false)
    }
  }

  const handleBatchDetect = async () => {
    const uploadedVideos = videos.filter(v => v.status === 'uploaded' && v.video_id)
    
    if (uploadedVideos.length === 0) {
      message.warning('没有可检测的视频')
      return
    }

    setProcessing(true)

    try {
      // 并行处理最多3个视频的检测
      const chunkSize = 3
      for (let i = 0; i < uploadedVideos.length; i += chunkSize) {
        const chunk = uploadedVideos.slice(i, i + chunkSize)
        
        await Promise.all(chunk.map(async (video) => {
          try {
            updateVideoStatus(video.video_id!, { status: 'detecting', progress: 0 })
            
            // 获取视频帧用于检测
            await getVideoFrames(video.video_id!)
            
            updateVideoStatus(video.video_id!, { status: 'detected', progress: 100 })
          } catch (error) {
            updateVideoStatus(video.video_id!, { 
              status: 'failed', 
              error: '检测失败' 
            })
          }
        }))
      }

      message.success('批量检测完成，请手动标记水印区域')
    } catch (error) {
      message.error('批量检测失败')
      console.error(error)
    } finally {
      setProcessing(false)
    }
  }

  const handleBatchProcess = () => {
    const detectedVideos = videos.filter(v => 
      v.status === 'detected' && v.video_id && selectedRowKeys.includes(v.id)
    )

    if (detectedVideos.length === 0) {
      message.warning('请选择已检测的视频')
      return
    }

    setBatchParamsVisible(true)
  }

  const handleBatchProcessSubmit = async () => {
    const values = await form.validateFields()
    
    const detectedVideos = videos.filter(v => 
      v.status === 'detected' && v.video_id && selectedRowKeys.includes(v.id)
    )

    setProcessing(true)
    setBatchParamsVisible(false)

    try {
      // 构建批量处理任务
      const tasks = detectedVideos.map(video => ({
        video_id: video.video_id!,
        mode: values.mode,
        regions: video.watermarkRegions || [],
        custom_logo: values.custom_logo
      }))

      // 调用批量去除API
      await batchRemoveWatermark(tasks)

      message.success('批量处理任务已提交，请在任务管理页面查看进度')
    } catch (error) {
      message.error('批量处理失败')
      console.error(error)
    } finally {
      setProcessing(false)
    }
  }

  const handleBatchDownload = () => {
    const completedVideos = videos.filter(v => 
      v.status === 'completed' && v.outputPath && selectedRowKeys.includes(v.id)
    )

    if (completedVideos.length === 0) {
      message.warning('没有可下载的视频')
      return
    }

    // 下载所有完成的视频
    completedVideos.forEach(video => {
      if (video.video_id) {
        const link = document.createElement('a')
        link.href = `/api/videos/${video.video_id}/output`
        link.download = video.name.replace(/\.[^/.]+$/, '_processed.mp4')
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
    })

    message.success(`开始下载 ${completedVideos.length} 个视频`)
  }

  const handleDelete = (id: string) => {
    setVideos(prev => prev.filter(v => v.id !== id))
    setSelectedRowKeys(prev => prev.filter(k => k !== id))
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      width: 250,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      render: (size: number) => `${(size / 1024 / 1024).toFixed(2)} MB`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const colorMap = {
          pending: 'default',
          uploading: 'processing',
          uploaded: 'success',
          detecting: 'processing',
          detected: 'success',
          processing: 'processing',
          completed: 'success',
          failed: 'error',
        }
        const textMap = {
          pending: '等待中',
          uploading: '上传中',
          uploaded: '已上传',
          detecting: '检测中',
          detected: '已检测',
          processing: '处理中',
          completed: '已完成',
          failed: '失败',
        }
        return (
          <Tag color={colorMap[status as keyof typeof colorMap]}>
            {textMap[status as keyof typeof textMap]}
          </Tag>
        )
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record: BatchVideo) => (
        <Progress 
          percent={progress} 
          status={record.status === 'failed' ? 'exception' : undefined}
          size="small"
        />
      ),
    },
    {
      title: '错误信息',
      dataIndex: 'error',
      key: 'error',
      render: (error?: string) => error || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: BatchVideo) => (
        <Button 
          type="link" 
          danger 
          icon={<DeleteOutlined />}
          onClick={() => handleDelete(record.id)}
          size="small"
        >
          删除
        </Button>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys as string[]),
    getCheckboxProps: (record: BatchVideo) => ({
      disabled: record.status === 'pending' || record.status === 'uploading' || record.status === 'failed',
    }),
  }

  return (
    <div>
      <Card 
        title="批量处理" 
        extra={
          <Space>
            <Button 
              icon={<PlayCircleOutlined />}
              onClick={handleBatchDetect}
              disabled={videos.length === 0 || processing}
              loading={processing}
            >
              批量检测
            </Button>
            <Button 
              type="primary"
              onClick={handleBatchProcess}
              disabled={selectedRowKeys.length === 0 || processing}
            >
              批量去除
            </Button>
            <Button 
              icon={<DownloadOutlined />}
              onClick={handleBatchDownload}
              disabled={selectedRowKeys.length === 0}
            >
              批量下载
            </Button>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 文件上传区域 */}
          <Card title="选择文件" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload
                fileList={fileList}
                onChange={({ fileList }) => setFileList(fileList)}
                beforeUpload={() => false}
                accept=".mp4,.avi,.mov,.mkv"
                multiple
                maxCount={50}
              >
                <Button icon={<UploadOutlined />}>选择视频文件</Button>
              </Upload>
              <div style={{ color: '#666', fontSize: '12px' }}>
                支持 MP4、AVI、MOV、MKV 格式，最多50个文件，单个文件不超过 5GB
              </div>
              <Button 
                type="primary" 
                onClick={handleUpload}
                loading={processing}
                disabled={fileList.length === 0}
              >
                开始上传
              </Button>
            </Space>
          </Card>

          {/* 批量处理列表 */}
          {videos.length > 0 && (
            <Card 
              title={`处理列表 (${videos.length}个视频)`}
              size="small"
              extra={
                <span style={{ fontSize: '12px', color: '#666' }}>
                  已选择 {selectedRowKeys.length} 个视频
                </span>
              }
            >
              <Table
                columns={columns}
                dataSource={videos}
                rowKey="id"
                rowSelection={rowSelection}
                pagination={{ pageSize: 10 }}
                scroll={{ x: 1000 }}
              />
            </Card>
          )}
        </Space>
      </Card>

      {/* 批量处理参数设置 */}
      <Modal
        title="批量处理参数"
        open={batchParamsVisible}
        onOk={handleBatchProcessSubmit}
        onCancel={() => setBatchParamsVisible(false)}
        okText="开始处理"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="处理模式"
            name="mode"
            initialValue="crop_reconstruct"
            rules={[{ required: true, message: '请选择处理模式' }]}
          >
            <Select>
              <Select.Option value="crop_reconstruct">裁剪重构</Select.Option>
              <Select.Option value="ai_inpainting">AI修复填充</Select.Option>
              <Select.Option value="blur_replace">局部模糊替换</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            label="说明"
            style={{ marginBottom: 0 }}
          >
            <div style={{ fontSize: '12px', color: '#666' }}>
              将对所有选中的视频应用相同的处理参数。如需单独调整，请在水印去除页面处理。
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default BatchProcessing
