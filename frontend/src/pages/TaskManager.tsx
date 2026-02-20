import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Tag, Progress, message } from 'antd'
import { ReloadOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { ProcessingTask } from '@/types'

/**
 * 任务管理页面
 * 显示所有处理任务的状态和进度
 */
const TaskManager: React.FC = () => {
  const navigate = useNavigate()
  const [tasks] = useState<ProcessingTask[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadTasks()
    // 定时刷新任务状态
    const interval = setInterval(loadTasks, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadTasks = async () => {
    setLoading(true)
    try {
      // TODO: 调用API获取任务列表
      // const response = await api.get('/tasks')
      // setTasks(response.data)
      message.info('任务列表加载功能待实现')
    } catch (error) {
      message.error('加载任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (_taskId: string) => {
    try {
      // TODO: 调用API删除任务
      message.success('删除成功')
      loadTasks()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
    },
    {
      title: '视频ID',
      dataIndex: 'video_id',
      key: 'video_id',
      width: 200,
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          detection: '水印检测',
          removal: '水印去除',
          optimization: '视频优化',
        }
        return typeMap[type] || type
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
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
      render: (record: ProcessingTask) => {
        if (record.status === 'completed') return <Progress percent={100} size="small" />
        if (record.status === 'failed') return <Progress percent={0} status="exception" size="small" />
        if (record.status === 'processing') return <Progress percent={50} status="active" size="small" />
        return <Progress percent={0} size="small" />
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      render: (time?: string) => time || '-',
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      render: (error?: string) => error || '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (record: ProcessingTask) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => navigate(`/videos/${record.video_id}`)}
          >
            查看
          </Button>
          <Button 
            type="link" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.task_id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card 
        title="任务管理" 
        extra={
          <Button 
            icon={<ReloadOutlined />}
            onClick={loadTasks}
            loading={loading}
          >
            刷新
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          loading={loading}
          rowKey="task_id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default TaskManager
