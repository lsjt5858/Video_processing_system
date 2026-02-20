import { useState } from 'react'
import { Card, Upload, Button, Table, Space, Tag, message, Progress } from 'antd'
import { UploadOutlined, PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'

interface BatchVideo {
  id: string
  name: string
  size: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
}

/**
 * 批量处理页面
 * 支持批量上传、检测和导出视频
 */
const BatchProcessing: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [videos, setVideos] = useState<BatchVideo[]>([])
  const [processing, setProcessing] = useState(false)

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择视频文件')
      return
    }

    if (fileList.length > 50) {
      message.error('最多支持50个文件')
      return
    }

    setProcessing(true)

    // 转换文件列表为批量视频对象
    const batchVideos: BatchVideo[] = fileList.map((file, index) => ({
      id: `video_${index}`,
      name: file.name,
      size: file.size || 0,
      status: 'pending',
      progress: 0,
    }))

    setVideos(batchVideos)

    try {
      // TODO: 实现批量上传逻辑
      // 模拟上传进度
      for (let i = 0; i < batchVideos.length; i++) {
        setVideos(prev => prev.map((v, idx) => 
          idx === i ? { ...v, status: 'uploading', progress: 50 } : v
        ))
        await new Promise(resolve => setTimeout(resolve, 1000))
        setVideos(prev => prev.map((v, idx) => 
          idx === i ? { ...v, status: 'completed', progress: 100 } : v
        ))
      }

      message.success('批量上传功能待实现')
    } catch (error) {
      message.error('批量上传失败')
    } finally {
      setProcessing(false)
    }
  }

  const handleBatchDetect = async () => {
    try {
      // TODO: 调用API批量检测水印
      message.success('批量检测功能待实现')
    } catch (error) {
      message.error('批量检测失败')
    }
  }

  const handleBatchExport = async () => {
    try {
      // TODO: 调用API批量导出
      message.success('批量导出功能待实现')
    } catch (error) {
      message.error('批量导出失败')
    }
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => `${(size / 1024 / 1024).toFixed(2)} MB`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap = {
          pending: 'default',
          uploading: 'processing',
          processing: 'processing',
          completed: 'success',
          failed: 'error',
        }
        const textMap = {
          pending: '等待中',
          uploading: '上传中',
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
  ]

  return (
    <div>
      <Card 
        title="批量处理" 
        extra={
          <Space>
            <Button 
              icon={<PlayCircleOutlined />}
              onClick={handleBatchDetect}
              disabled={videos.length === 0}
            >
              批量检测
            </Button>
            <Button 
              icon={<DownloadOutlined />}
              onClick={handleBatchExport}
              disabled={videos.length === 0}
            >
              批量导出
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
            <Card title="处理列表" size="small">
              <Table
                columns={columns}
                dataSource={videos}
                rowKey="id"
                pagination={false}
              />
            </Card>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default BatchProcessing
