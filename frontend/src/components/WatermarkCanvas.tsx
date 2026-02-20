import { useRef, useState, useEffect } from 'react'
import { message } from 'antd'
import type { WatermarkRegion, BoundingBox } from '@/types'

interface WatermarkCanvasProps {
  videoId: string
  frameUrl: string
  currentTime: number
  videoDuration: number
  onRegionMarked: (region: WatermarkRegion) => void
  markingMode: boolean
  existingRegions: WatermarkRegion[]
}

/**
 * 水印标记画布组件
 * 功能：
 * 1. 显示视频帧
 * 2. 鼠标拖拽绘制矩形框
 * 3. 显示已标记的水印区域
 * 4. 支持多个矩形框
 */
const WatermarkCanvas: React.FC<WatermarkCanvasProps> = ({ 
  videoId,
  frameUrl,
  currentTime,
  videoDuration,
  onRegionMarked,
  markingMode,
  existingRegions,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement | null>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null)
  const [currentBox, setCurrentBox] = useState<BoundingBox | null>(null)
  const [imageLoaded, setImageLoaded] = useState(false)

  // 加载视频帧图片
  useEffect(() => {
    if (!frameUrl) return

    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      imageRef.current = img
      setImageLoaded(true)
      drawCanvas()
    }
    img.onerror = () => {
      message.error('加载视频帧失败')
      setImageLoaded(false)
    }
    img.src = frameUrl
  }, [frameUrl])

  // 绘制画布
  useEffect(() => {
    if (imageLoaded) {
      drawCanvas()
    }
  }, [imageLoaded, currentBox, existingRegions])

  /**
   * 绘制画布内容
   */
  const drawCanvas = () => {
    const canvas = canvasRef.current
    const img = imageRef.current
    if (!canvas || !img) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 设置画布大小为图片大小
    canvas.width = img.width
    canvas.height = img.height

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 绘制视频帧
    ctx.drawImage(img, 0, 0)

    // 绘制已存在的水印区域
    existingRegions.forEach((region, index) => {
      ctx.strokeStyle = '#52c41a'
      ctx.lineWidth = 2
      ctx.setLineDash([])
      ctx.strokeRect(region.bbox.x, region.bbox.y, region.bbox.width, region.bbox.height)
      
      // 填充半透明背景
      ctx.fillStyle = 'rgba(82, 196, 26, 0.1)'
      ctx.fillRect(region.bbox.x, region.bbox.y, region.bbox.width, region.bbox.height)
      
      // 绘制区域编号
      ctx.fillStyle = '#52c41a'
      ctx.font = 'bold 14px Arial'
      ctx.fillText(`#${index + 1}`, region.bbox.x + 5, region.bbox.y + 20)
    })

    // 绘制当前正在绘制的框
    if (currentBox && markingMode) {
      ctx.strokeStyle = '#ff4d4f'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 5])
      ctx.strokeRect(currentBox.x, currentBox.y, currentBox.width, currentBox.height)
      
      // 填充半透明背景
      ctx.fillStyle = 'rgba(255, 77, 79, 0.2)'
      ctx.fillRect(currentBox.x, currentBox.y, currentBox.width, currentBox.height)
      
      // 显示尺寸信息
      ctx.fillStyle = '#ff4d4f'
      ctx.font = 'bold 12px Arial'
      ctx.fillText(
        `${currentBox.width} × ${currentBox.height}`, 
        currentBox.x, 
        currentBox.y - 5
      )
    }
  }

  /**
   * 获取鼠标在画布上的坐标
   */
  const getCanvasCoordinates = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }

    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    
    return {
      x: Math.round((e.clientX - rect.left) * scaleX),
      y: Math.round((e.clientY - rect.top) * scaleY),
    }
  }

  /**
   * 鼠标按下事件
   */
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!markingMode) return

    const coords = getCanvasCoordinates(e)
    setIsDrawing(true)
    setStartPos(coords)
    setCurrentBox(null)
  }

  /**
   * 鼠标移动事件
   */
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPos || !markingMode) return

    const coords = getCanvasCoordinates(e)
    const width = coords.x - startPos.x
    const height = coords.y - startPos.y

    setCurrentBox({
      x: width > 0 ? startPos.x : coords.x,
      y: height > 0 ? startPos.y : coords.y,
      width: Math.abs(width),
      height: Math.abs(height),
    })
  }

  /**
   * 鼠标释放事件
   */
  const handleMouseUp = () => {
    if (!isDrawing || !currentBox || !markingMode) {
      setIsDrawing(false)
      return
    }

    setIsDrawing(false)

    // 验证框选区域大小
    if (currentBox.width < 10 || currentBox.height < 10) {
      message.warning('框选区域太小，请重新框选（最小10x10像素）')
      setCurrentBox(null)
      setStartPos(null)
      return
    }

    // 创建水印区域对象
    const region: WatermarkRegion = {
      region_id: `region_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      video_id: videoId,
      bbox: currentBox,
      start_time: currentTime,
      end_time: videoDuration,
      confidence: 1.0,
      watermark_type: 'manual',
      detection_method: 'manual',
    }

    onRegionMarked(region)
    setCurrentBox(null)
    setStartPos(null)
    message.success('水印区域已标记')
  }

  /**
   * 鼠标离开画布
   */
  const handleMouseLeave = () => {
    if (isDrawing) {
      setIsDrawing(false)
      setCurrentBox(null)
      setStartPos(null)
    }
  }

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        style={{
          cursor: markingMode ? 'crosshair' : 'default',
          border: markingMode ? '2px solid #1890ff' : '1px solid #d9d9d9',
          borderRadius: '4px',
          maxWidth: '100%',
          display: 'block',
        }}
      />
      {!imageLoaded && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: '#999',
        }}>
          加载中...
        </div>
      )}
    </div>
  )
}

export default WatermarkCanvas
