import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Tag, Progress, message, Modal, Descriptions, Select, DatePicker, Input } from 'antd'
import { ReloadOutlined, EyeOutlined, DeleteOutlined, RedoOutlined, DownloadOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getTasks, getTaskStatus, downloadProcessedVideo } from '@/services/api'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { ProcessingTask } from '@/types'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

/**
 * 任务管理页面
 * 显示所有处理任务的状态和进度
 */
const TaskManager: React.FC = () => {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState<ProcessingTask[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTask, setSelectedTask] = useState<ProcessingTask | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })

  // 筛选条件
  const [filters, setFilters] = useState({
    status: undefined as string | undefined,
    task_type: undefined as string | undefined,
    date_range: undefined as [dayjs.Dayjs, dayjs.Dayjs] | undefined,
    search: undefined as string | undefined,
  })

  // WebSocket连接用于实时更新任务状态
  const { lastMessage } = useWebSocket('ws://localhost:8000/ws/tasks', {
    onMessage: (data) => {
      if (data.type === 'task_update') {
        // 更新任务列表中的任务状态
        setTasks(prev => prev.map(task =>
          task.task_id === data.task_id ? { ...task, ...data.task } : task
        ))
      } else if (data.type === 'task_complete') {
        // 任务完成，刷新列表
        loadTasks()
      }
    },
    onError: () => {
      console.warn('WebSocket 连接错误，将使用轮询方式')
    },
    reconnect: true,
    maxReconnectAttempts: 3,
  })

  useEffect(() => {
    loadTasks()
    // 定时刷新任务状态（每30秒）
    const interval = setInterval(loadTasks, 30000)
    return () => clearInterval(interval)
  }, [pagination.current, pagination.pageSize, filters])

  const loadTasks = async () => {
    setLoading(true)
    try {
      const params: any = {
        page: pagination.current,
        page_size: pagination.pageSize,
      }

      // 添加筛选条件
      if (filters.status) params.status = filters.status
      if (filters.task_type) params.task_type = filters.task_type
      if (filters.search) params.search = filters.search
      if (filters.date_range) {
        params.start_date = filters.date_range[0].format('YYYY-MM-DD')
        params.end_date = filters.date_range[1].format('YYYY-MM-DD')
      }

      const response = await getTasks(params)
      setTasks(response.tasks || [])
      setPagination(prev => ({ ...prev, total: response.total || 0 }))
    } catch (error) {
      message.error('加载任务列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    loadTasks()
    message.success('已刷新')
  }

  const handleViewDetail = async (task: ProcessingTask) => {
    try {
      // 获取最新的任务详情
      const latestTask = await getTaskStatus(task.task_id)
      setSelectedTask(latestTask)
      setDetailVisible(true)
    } catch (error) {
      message.error('获取任务详情失败')
      console.error(error)
    }
  }

  const handleRetry = async (taskId: string) => {
    try {
      // TODO: 实现任务重试API
      message.info('任务重试功能待后端实现')
      // await api.post(`/tasks/${taskId}/retry`)
      // message.success('任务已重新提交')
      // loadTasks()
    } catch (error) {
      message.error('重试失败')
      console.error(error)
    }
  }

  const handleCancel = async (taskId: string) => {
    Modal.confirm({
      title: '确认取消',
      content: '确定要取消这个任务吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          // TODO: 实现任务取消API
          message.info('任务取消功能待后端实现')
          // await api.post(`/tasks/${taskId}/cancel`)
          // message.success('任务已取消')
          // loadTasks()
        } catch (error) {
          message.error('取消失败')
          console.error(error)
        }
      }
    })
  }

  const handleDelete = async (taskId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个任务吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          // TODO: 实现任务删除API
          message.info('任务删除功能待后端实现')
          // await api.delete(`/tasks/${taskId}`)
          // message.success('删除成功')
          // loadTasks()
        } catch (error) {
          message.error('删除失败')
          console.error(error)
        }
      }
    })
  }

  const handleDownload = (videoId: string, taskId: string) => {
    const link = document.createElement('a')
    link.href = `/api/videos/${videoId}/output`
    link.download = `processed_${taskId}.mp4`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    message.success('开始下载')
  }

  const handleTableChange = (newPagination: any) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
      total: pagination.total,
    })
  }

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, current: 1 })) // 重置到第一页
  }

  const handleResetFilters = () => {
    setFilters({
      status: undefined,
      task_type: undefined,
      date_range: undefined,
      search: undefined,
    })
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 180,
      ellipsis: true,
    },
    {
      title: '视频ID',
      dataIndex: 'video_id',
      key: 'video_id',
      width: 180,
      ellipsis: true,
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 120,
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          detection: '水印检测',
          removal: '水印去除',
          optimization: '视频优化',
          batch_detection: '批量检测',
          batch_removal: '批量去除',
        }
        return typeMap[type] || type
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const colorMap = {
          pending: 'default',
          processing: 'processing',
          completed: 'success',
          failed: 'error',
        }
        const textMap = {
          pending: '等待中',
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
      key: 'progress',
      width: 150,
      render: (record: ProcessingTask) => {
        if (record.status === 'completed') return <Progress percent={100} size="small" />
        if (record.status === 'failed') return <Progress percent={0} status="exception" size="small" />
        if (record.status === 'processing') {
          // 如果有进度信息，显示实际进度
          const progress = record.result?.progress || 50
          return <Progress percent={progress} status="active" size="small" />
        }
        return <Progress percent={0} size="small" />
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 160,
      render: (time?: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      fixed: 'right' as const,
      render: (record: ProcessingTask) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
            size="small"
          >
            详情
          </Button>
          {record.status === 'completed' && (
            <Button
              type="link"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record.video_id, record.task_id)}
              size="small"
            >
              下载
            </Button>
          )}
          {record.status === 'failed' && (
            <Button
              type="link"
              icon={<RedoOutlined />}
              onClick={() => handleRetry(record.task_id)}
              size="small"
            >
              重试
            </Button>
          )}
          {record.status === 'processing' && (
            <Button
              type="link"
              danger
              onClick={() => handleCancel(record.task_id)}
              size="small"
            >
              取消
            </Button>
          )}
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.task_id)}
            size="small"
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div className="fade-in">
      <Card
        title={<span style={{ fontWeight: 700, fontSize: '18px', color: '#1e293b' }}>任务管理</span>}
        className="glass-card"
        bordered={false}
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        }
      >
        {/* 筛选条件 */}
        <Space style={{ marginBottom: 16 }} wrap>
          <Select
            placeholder="任务状态"
            style={{ width: 120 }}
            allowClear
            value={filters.status}
            onChange={(value) => handleFilterChange('status', value)}
          >
            <Select.Option value="pending">等待中</Select.Option>
            <Select.Option value="processing">处理中</Select.Option>
            <Select.Option value="completed">已完成</Select.Option>
            <Select.Option value="failed">失败</Select.Option>
          </Select>

          <Select
            placeholder="任务类型"
            style={{ width: 120 }}
            allowClear
            value={filters.task_type}
            onChange={(value) => handleFilterChange('task_type', value)}
          >
            <Select.Option value="detection">水印检测</Select.Option>
            <Select.Option value="removal">水印去除</Select.Option>
            <Select.Option value="optimization">视频优化</Select.Option>
            <Select.Option value="batch_detection">批量检测</Select.Option>
            <Select.Option value="batch_removal">批量去除</Select.Option>
          </Select>

          <RangePicker
            placeholder={['开始日期', '结束日期']}
            value={filters.date_range}
            onChange={(dates) => handleFilterChange('date_range', dates as any)}
          />

          <Input
            placeholder="搜索任务ID或视频ID"
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            allowClear
          />

          <Button onClick={handleResetFilters}>重置</Button>
        </Space>

        {/* 任务列表 */}
        <Table
          columns={columns}
          dataSource={tasks}
          loading={loading}
          rowKey="task_id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1400 }}
        />
      </Card>

      {/* 任务详情弹窗 */}
      <Modal
        title="任务详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
          selectedTask?.status === 'completed' && (
            <Button
              key="download"
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => {
                if (selectedTask) {
                  handleDownload(selectedTask.video_id, selectedTask.task_id)
                }
              }}
            >
              下载结果
            </Button>
          ),
          selectedTask?.status === 'failed' && (
            <Button
              key="retry"
              type="primary"
              icon={<RedoOutlined />}
              onClick={() => {
                if (selectedTask) {
                  handleRetry(selectedTask.task_id)
                  setDetailVisible(false)
                }
              }}
            >
              重试
            </Button>
          ),
        ]}
        width={700}
      >
        {selectedTask && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="任务ID">{selectedTask.task_id}</Descriptions.Item>
            <Descriptions.Item label="视频ID">
              <Button
                type="link"
                onClick={() => {
                  navigate(`/videos/${selectedTask.video_id}`)
                  setDetailVisible(false)
                }}
              >
                {selectedTask.video_id}
              </Button>
            </Descriptions.Item>
            <Descriptions.Item label="任务类型">
              {selectedTask.task_type === 'detection' && '水印检测'}
              {selectedTask.task_type === 'removal' && '水印去除'}
              {selectedTask.task_type === 'optimization' && '视频优化'}
              {selectedTask.task_type === 'batch_detection' && '批量检测'}
              {selectedTask.task_type === 'batch_removal' && '批量去除'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={
                selectedTask.status === 'completed' ? 'success' :
                  selectedTask.status === 'failed' ? 'error' :
                    selectedTask.status === 'processing' ? 'processing' : 'default'
              }>
                {selectedTask.status === 'pending' && '等待中'}
                {selectedTask.status === 'processing' && '处理中'}
                {selectedTask.status === 'completed' && '已完成'}
                {selectedTask.status === 'failed' && '失败'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {dayjs(selectedTask.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            {selectedTask.started_at && (
              <Descriptions.Item label="开始时间">
                {dayjs(selectedTask.started_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            )}
            {selectedTask.completed_at && (
              <Descriptions.Item label="完成时间">
                {dayjs(selectedTask.completed_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="处理参数">
              <pre style={{ margin: 0, fontSize: '12px' }}>
                {JSON.stringify(selectedTask.parameters, null, 2)}
              </pre>
            </Descriptions.Item>
            {selectedTask.error_message && (
              <Descriptions.Item label="错误信息">
                <span style={{ color: 'red' }}>{selectedTask.error_message}</span>
              </Descriptions.Item>
            )}
            {selectedTask.result && (
              <Descriptions.Item label="处理结果">
                <pre style={{ margin: 0, fontSize: '12px' }}>
                  {JSON.stringify(selectedTask.result, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default TaskManager
