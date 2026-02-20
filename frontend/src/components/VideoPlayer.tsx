import { useRef, useEffect } from 'react'
import { Empty } from 'antd'

interface VideoPlayerProps {
  videoUrl: string
  width?: string | number
  height?: string | number
  controls?: boolean
  autoPlay?: boolean
}

/**
 * 视频播放器组件
 * 用于预览视频内容
 */
const VideoPlayer: React.FC<VideoPlayerProps> = ({ 
  videoUrl, 
  width = '100%',
  height = 'auto',
  controls = true,
  autoPlay = false
}) => {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current && videoUrl) {
      videoRef.current.load()
    }
  }, [videoUrl])

  if (!videoUrl) {
    return (
      <div style={{ 
        width, 
        height: height === 'auto' ? 400 : height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f0f0'
      }}>
        <Empty description="暂无视频" />
      </div>
    )
  }

  return (
    <video
      ref={videoRef}
      width={width}
      height={height}
      controls={controls}
      autoPlay={autoPlay}
      style={{ 
        maxWidth: '100%',
        background: '#000'
      }}
    >
      <source src={videoUrl} type="video/mp4" />
      您的浏览器不支持视频播放
    </video>
  )
}

export default VideoPlayer
