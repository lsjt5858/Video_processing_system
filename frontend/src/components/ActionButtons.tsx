import { Button, Dropdown, Tooltip, Space } from 'antd'
import type { MenuProps } from 'antd'
import {
  PlayCircleOutlined,
  EditOutlined,
  ScissorOutlined,
  DeleteOutlined,
  MoreOutlined,
  EyeOutlined,
} from '@ant-design/icons'

interface ActionButtonsProps {
  videoId: string
  filename: string
  onView?: () => void
  onMark?: () => void
  onRemove?: () => void
  onDelete?: () => void
  compact?: boolean
}

/**
 * 视频操作按钮组件
 * 提供统一的操作按钮样式和交互
 */
const ActionButtons: React.FC<ActionButtonsProps> = ({
  videoId,
  filename,
  onView,
  onMark,
  onRemove,
  onDelete,
  compact = true,
}) => {
  // 下拉菜单项
  const menuItems: MenuProps['items'] = [
    {
      key: 'view',
      icon: <EyeOutlined />,
      label: '查看详情',
      onClick: onView,
    },
    {
      key: 'mark',
      icon: <EditOutlined />,
      label: '标记水印',
      onClick: onMark,
    },
    {
      key: 'remove',
      icon: <ScissorOutlined />,
      label: '去除水印',
      onClick: onRemove,
    },
    {
      type: 'divider',
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除',
      danger: true,
      onClick: onDelete,
    },
  ]

  // 紧凑模式 - 只显示图标按钮
  if (compact) {
    return (
      <Space size={4} className="action-buttons-compact">
        <Tooltip title="查看详情" placement="top">
          <Button
            type="text"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={onView}
            className="action-icon-btn"
          />
        </Tooltip>
        <Tooltip title="标记水印" placement="top">
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={onMark}
            className="action-icon-btn"
          />
        </Tooltip>
        <Tooltip title="去除水印" placement="top">
          <Button
            type="primary"
            size="small"
            icon={<ScissorOutlined />}
            onClick={onRemove}
            className="action-icon-btn action-primary"
          />
        </Tooltip>
        <Dropdown menu={{ items: menuItems }} trigger={['click']} placement="bottomRight">
          <Tooltip title="更多操作" placement="top">
            <Button
              type="text"
              size="small"
              icon={<MoreOutlined />}
              className="action-icon-btn"
            />
          </Tooltip>
        </Dropdown>
      </Space>
    )
  }

  // 完整模式 - 显示文字按钮
  return (
    <Space size="small" className="action-buttons">
      <Button
        type="default"
        size="small"
        icon={<PlayCircleOutlined />}
        onClick={onView}
        className="action-secondary"
      >
        查看
      </Button>
      <Button
        type="default"
        size="small"
        icon={<EditOutlined />}
        onClick={onMark}
        className="action-secondary"
      >
        标记
      </Button>
      <Button
        type="primary"
        size="small"
        icon={<ScissorOutlined />}
        onClick={onRemove}
        className="action-primary"
      >
        去除水印
      </Button>
      <Button
        type="default"
        danger
        size="small"
        icon={<DeleteOutlined />}
        onClick={onDelete}
        className="action-danger"
      >
        删除
      </Button>
    </Space>
  )
}

export default ActionButtons
