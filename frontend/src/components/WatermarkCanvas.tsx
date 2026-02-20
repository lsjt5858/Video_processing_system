import { useRef, useState, useEffect } from 'react'
import { message } from 'antd'
import type { WatermarkRegion, BoundingBox } from '@/types'

interface WatermarkCanvasProps {
  videoId: string
  onRegionMarked: (region: WatermarkRegion) => void
}

/**
 * 水印标记画布组件
 * 用于手动框选水印区域
 */
const WatermarkCanvas: React.FC<WatermarkCanvasProps> = ({ 
  videoId,
  onRegionMarked 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null)
  const [currentBox, setCurrentBox] = useState<BoundingBox | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 绘制当前框选区域
    if (currentBox) {
      ctx.strokeStyle = '#ff4d4f'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 5])
      ctx.strokeRect(currentBox.x, currentBox.y, currentBox.width, currentBox.height)
      
      // 填充半透明背景
      ctx.fillStyle = 'rgba(255, 77, 79, 0.1)'
      ctx.fillRect(currentBox.x, currentBox.y, currentBox.width, currentBox.height)
    }
  }, [currentBox])

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    setIsDrawing(true)
    setStartPos({ x, y })
    setCurrentBox(null)
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPos) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const width = x - startPos.x
    const height = y - startPos.y

    setCurrentBox({
      x: width > 0 ? startPos.x : x,
      y: height > 0 ? startPos.y : y,
      width: Math.abs(width),
      height: Math.abs(height),
    })
  }

  const handleMouseUp = () => {
    if (!isDrawing || !currentBox) return

    setIsDrawing(false)

    // 验证框选区域大小
    if (currentBox.width < 10 || currentBox.height < 10) {
      message.warning('框选区域太小，请重新框选')
      setCurrentBox(null)
      return
    }

    // 创建水印区域对象
    const region: WatermarkRegion = {
      region_id: `region_${Date.now()}`,
      video_id: videoId,
      bbox: currentBox,
      start_time: 0, // TODO: 从视频播放器获取当前时间
      end_time: 0, // TODO: 从视频播放器获取视频总时长
      confidence: 1.0,
      watermark_type: 'manual',
      detection_method: 'manual',
    }

    onRegionMarked(region)
    setCurrentBox(null)
    setStartPos(null)
  }

  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={450}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        cursor: 'crosshair',
        border: '2px dashed #1890ff',
      }}
    />
  )
}

export default WatermarkCanvas
