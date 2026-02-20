import { Progress } from 'antd'
import type { ProgressProps } from 'antd'

interface ProgressBarProps extends ProgressProps {
  percent: number
  status?: 'success' | 'exception' | 'normal' | 'active'
  showInfo?: boolean
}

/**
 * 进度条组件
 * 用于显示任务处理进度
 */
const ProgressBar: React.FC<ProgressBarProps> = ({ 
  percent, 
  status = 'normal',
  showInfo = true,
  ...rest 
}) => {
  return (
    <Progress 
      percent={percent} 
      status={status}
      showInfo={showInfo}
      strokeColor={{
        '0%': '#108ee9',
        '100%': '#87d068',
      }}
      {...rest}
    />
  )
}

export default ProgressBar
