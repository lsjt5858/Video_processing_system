import { Card } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'

interface VideoThumbnailProps {
  videoId: string
  thumbnailUrl?: string
  title?: string
  duration?: number
  onClick?: () => void
}

/**
 * 视频缩略图组件
 * 用于在列表中显示视频预览
 */
const VideoThumbnail: React.FC<VideoThumbnailProps> = ({ 
  videoId,
  thumbnailUrl, 
  title,
  duration,
  onClick 
}) => {
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '00:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <Card
      hoverable
      onClick={onClick}
      cover={
        <div style={{ 
          position: 'relative',
          paddingTop: '56.25%', // 16:9 aspect ratio
          background: '#f0f0f0',
          overflow: 'hidden'
        }}>
          {thumbnailUrl ? (
            <img 
              src={thumbnailUrl} 
              alt={title}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
            />
          ) : (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '48px',
              color: '#999'
            }}>
              <PlayCircleOutlined />
            </div>
          )}
          {duration && (
            <div style={{
              position: 'absolute',
              bottom: 8,
              right: 8,
              background: 'rgba(0, 0, 0, 0.7)',
              color: 'white',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              {formatDuration(duration)}
            </div>
          )}
        </div>
      }
    >
      <Card.Meta 
        title={title || `视频 ${videoId}`}
        description={`ID: ${videoId}`}
      />
    </Card>
  )
}

export default VideoThumbnail
