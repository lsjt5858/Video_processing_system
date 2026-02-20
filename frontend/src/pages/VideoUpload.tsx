import { useState, useEffect } from 'react'
import { 
  Card, 
  Upload, 
  Button, 
  Form, 
  Input, 
  Tabs, 
  Space, 
  message, 
  Progress, 
  List,
  Typography,
  Alert
} from 'antd'
import { 
  UploadOutlined, 
  LinkOutlined, 
  InboxOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { UploadFile, UploadProps } from 'antd'
import { uploadVideo, batchUploadVideos, downloadVideoFromUrl } from '@/services/api'
import { useWebSocket } from '@/hooks/useWebSocket'
import { 
  validateFileSize, 
  validateFileFormat, 
  validateUrl, 
  validateFiles,
  handleApiError,
  showErrorMessage,
  showErrorNotification
} from '@/utils/errorHandler'

const { Dragger } = Upload
const { Text } = Typography

interface FileUploadStatus {
  file: File
  status: 'uploading' | 'success' | 'error'
  progress: number
  videoId?: string
  error?: string
}

/**
 * 视频上传页面
 * 支持三种上传方式：本地上传、批量上传、URL下载
 */
const VideoUpload: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [fileStatuses, setFileStatuses] = useState<FileUploadStatus[]>([])
  const [urlDownloading, setUrlDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)
  const [urlError, setUrlError] = useState<string | null>(null)


  // WebSocket连接用于实时进度更新
  const clientId = `client_${Date.now()}`
  const wsUrl = `ws://localhost:8000/ws/${clientId}`
  
  const { isConnected } = useWebSocket(wsUrl, {
    onMessage: (data) => {
      console.log('WebSocket message:', data)
      
      // 处理上传进度更新
      if (data.type === 'upload_progress') {
        updateFileProgress(data.filename, data.progress)
      }
      
      // 处理下载进度更新
      if (data.type === 'download_progress') {
        setDownloadProgress(data.progress)
      }
      
      // 处理任务完成
      if (data.type === 'task_completed') {
        message.success(`任务完成: ${data.task_id}`)
      }
    },
    reconnect: true,
  })

  useEffect(() => {
    if (isConnected) {
      console.log('WebSocket connected')
    }
  }, [isConnected])

  // 更新单个文件的上传进度
  const updateFileProgress = (filename: string, progress: number) => {
    setFileStatuses(prev => 
      prev.map(item => 
        item.file.name === filename 
          ? { ...item, progress, status: progress === 100 ? 'success' : 'uploading' }
          : item
      )
    )
  }

  // 文件验证（使用新的错误处理工具）
  const validateFile = (file: File): boolean => {
    // 验证文件大小
    if (!validateFileSize(file, 5)) {
      return false
    }
    
    // 验证文件格式
    if (!validateFileFormat(file, ['mp4', 'avi', 'mov', 'mkv'])) {
      return false
    }
    
    return true
  }
    const maxSize = 5 * 1024 * 1024 * 1024 // 5GB

    // 检查文件格式
    const hasValidType = validFormats.includes(file.type)
    const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
    
    if (!hasValidType && !hasValidExtension) {
      message.error(`${file.name}: 不支持的文件格式，仅支持 MP4、AVI、MOV、MKV`)
      return false
    }

    // 检查文件大小
    if (file.size > maxSize) {
      message.error(`${file.name}: 文件大小超过 5GB 限制`)
      return false
    }

    return true
  }

  // 处理本地单文件上传
  const handleSingleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }

    const file = fileList[0].originFileObj as File
    if (!validateFile(file)) {
      return
    }

    setUploading(true)
    const status: FileUploadStatus = {
      file,
      status: 'uploading',
      progress: 0
    }
    setFileStatuses([status])

    try {
      await uploadVideo(file, (progress) => {
        setFileStatuses([{ ...status, progress }])
      })

      setFileStatuses([{ ...status, status: 'success', progress: 100 }])
      message.success('上传成功！')
      
      setTimeout(() => {
        navigate('/videos')
      }, 1500)
    } catch (error: any) {
      setFileStatuses([{ 
        ...status, 
        status: 'error', 
        progress: 0, 
        error: error.message || '上传失败' 
      }])
      message.error('上传失败')
    } finally {
      setUploading(false)
    }
  }

  // 处理批量上传
  const handleBatchUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }

    if (fileList.length > 50) {
      message.error('批量上传最多支持 50 个文件')
      return
    }

    // 验证所有文件
    const files = fileList.map(f => f.originFileObj as File)
    const validFiles = files.filter(validateFile)
    
    if (validFiles.length === 0) {
      return
    }

    setUploading(true)
    
    // 初始化所有文件状态
    const initialStatuses: FileUploadStatus[] = validFiles.map(file => ({
      file,
      status: 'uploading',
      progress: 0
    }))
    setFileStatuses(initialStatuses)

    try {
      // 使用批量上传API
      await batchUploadVideos(validFiles)
      
      // 更新所有文件为成功状态
      setFileStatuses(prev => 
        prev.map(item => ({
          ...item,
          status: 'success',
          progress: 100
        }))
      )
      
      message.success(`成功上传 ${validFiles.length} 个文件！`)
      
      setTimeout(() => {
        navigate('/videos')
      }, 2000)
    } catch (error: any) {
      message.error('批量上传失败')
      
      // 标记所有为失败
      setFileStatuses(prev => 
        prev.map(item => ({
          ...item,
          status: 'error',
          error: error.message || '上传失败'
        }))
      )
    } finally {
      setUploading(false)
    }
  }

  // 处理URL下载
  const handleUrlDownload = async (values: { url: string }) => {
    setUrlDownloading(true)
    setDownloadProgress(0)

    try {
      await downloadVideoFromUrl(values.url)
      
      setDownloadProgress(100)
      message.success('视频下载成功！')
      
      setTimeout(() => {
        navigate('/videos')
      }, 1500)
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || '下载失败，请检查URL是否有效')
    } finally {
      setUrlDownloading(false)
    }
  }

  // 移除文件
  const handleRemove = (removeFile: UploadFile) => {
    setFileList(prev => prev.filter(f => f.uid !== removeFile.uid))
  }

  // Upload组件配置
  const uploadProps: UploadProps = {
    fileList,
    onChange: ({ fileList: newFileList }) => setFileList(newFileList),
    beforeUpload: () => {
      // 不自动上传，手动控制
      return false
    },
    onRemove: handleRemove,
    accept: '.mp4,.avi,.mov,.mkv',
    multiple: true,
    maxCount: 50,
  }

  // 渲染文件上传状态列表
  const renderFileStatusList = () => {
    if (fileStatuses.length === 0) return null

    return (
      <Card title="上传进度" style={{ marginTop: 16 }}>
        <List
          dataSource={fileStatuses}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta
                avatar={
                  item.status === 'success' ? (
                    <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                  ) : item.status === 'error' ? (
                    <CloseCircleOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                  ) : null
                }
                title={item.file.name}
                description={
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text type="secondary">
                      大小: {(item.file.size / 1024 / 1024).toFixed(2)} MB
                    </Text>
                    {item.status === 'uploading' && (
                      <Progress percent={item.progress} status="active" />
                    )}
                    {item.status === 'success' && (
                      <Text type="success">上传成功</Text>
                    )}
                    {item.status === 'error' && (
                      <Text type="danger">{item.error || '上传失败'}</Text>
                    )}
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Card>
    )
  }

  return (
    <div>
      <Card title="视频上传">
        <Alert
          message="上传说明"
          description="支持 MP4、AVI、MOV、MKV 格式，单个文件不超过 5GB，批量上传上限为 50 个文件"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Tabs
          defaultActiveKey="single"
          items={[
            {
              key: 'single',
              label: (
                <span>
                  <UploadOutlined /> 单文件上传
                </span>
              ),
              children: (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Dragger {...uploadProps} maxCount={1}>
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                    <p className="ant-upload-hint">
                      支持单个视频文件上传，支持 MP4、AVI、MOV、MKV 格式
                    </p>
                  </Dragger>

                  <Space>
                    <Button 
                      type="primary" 
                      onClick={handleSingleUpload}
                      loading={uploading}
                      disabled={fileList.length === 0}
                    >
                      开始上传
                    </Button>
                    <Button autoInsertSpace={false} onClick={() => navigate('/videos')}>
                      取消
                    </Button>
                  </Space>

                  {renderFileStatusList()}
                </Space>
              ),
            },
            {
              key: 'batch',
              label: (
                <span>
                  <UploadOutlined /> 批量上传
                </span>
              ),
              children: (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Dragger {...uploadProps}>
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">点击或拖拽多个文件到此区域上传</p>
                    <p className="ant-upload-hint">
                      支持批量选择，最多 50 个文件，支持 MP4、AVI、MOV、MKV 格式
                    </p>
                  </Dragger>

                  {fileList.length > 0 && (
                    <Alert
                      message={`已选择 ${fileList.length} 个文件`}
                      type="info"
                      showIcon
                    />
                  )}

                  <Space>
                    <Button 
                      type="primary" 
                      onClick={handleBatchUpload}
                      loading={uploading}
                    >
                      开始批量上传
                    </Button>
                    <Button 
                      onClick={() => setFileList([])}
                      disabled={fileList.length === 0}
                    >
                      清空列表
                    </Button>
                    <Button autoInsertSpace={false} onClick={() => navigate('/videos')}>
                      取消
                    </Button>
                  </Space>

                  {renderFileStatusList()}
                </Space>
              ),
            },
            {
              key: 'url',
              label: (
                <span>
                  <LinkOutlined /> URL下载
                </span>
              ),
              children: (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleUrlDownload}
                  >
                    <Form.Item 
                      name="url" 
                      label="视频链接"
                      rules={[
                        { required: true, message: '请输入视频链接' },
                      ]}
                      validateStatus={urlError ? 'error' : undefined}
                      help={urlError || undefined}
                    >
                      <Input 
                        placeholder="请输入视频链接（支持 YouTube、Bilibili 等平台）" 
                        prefix={<LinkOutlined />}
                        size="large"
                        onChange={() => setUrlError(null)}
                      />
                    </Form.Item>

                    {urlDownloading && (
                      <Form.Item>
                        <Progress 
                          percent={downloadProgress} 
                          status="active"
                          format={(percent) => `下载中 ${percent}%`}
                        />
                      </Form.Item>
                    )}

                    <Form.Item>
                      <Space>
                        <Button 
                          type="primary" 
                          htmlType="button" 
                          loading={urlDownloading}
                          onClick={async () => {
                            const rawUrl = form.getFieldValue('url')
                            const url = typeof rawUrl === 'string' ? rawUrl.trim() : ''
                            if (!url) {
                              setUrlError('请输入视频链接')
                              return
                            }
                            try {
                              new URL(url)
                            } catch {
                              setUrlError('请输入有效的URL')
                              return
                            }
                            setUrlError(null)
                            await handleUrlDownload({ url })
                          }}
                        >
                          开始下载
                        </Button>
                        <Button autoInsertSpace={false} onClick={() => navigate('/videos')}>
                          取消
                        </Button>
                      </Space>
                    </Form.Item>
                  </Form>
                </Space>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}

export default VideoUpload
