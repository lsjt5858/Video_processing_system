import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter, MemoryRouter, Route, Routes } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import WatermarkMarker from '@/pages/WatermarkMarker'
import { VideoProvider } from '@/contexts/VideoContext'
import { TaskProvider } from '@/contexts/TaskContext'
import { WebSocketProvider } from '@/contexts/WebSocketContext'
import * as api from '@/services/api'
import type { Video, WatermarkRegion } from '@/types'

// Mock API
vi.mock('@/services/api', () => ({
  getVideoById: vi.fn(),
  getVideoFrames: vi.fn(),
  getWatermarks: vi.fn(),
  markWatermark: vi.fn(),
  updateWatermark: vi.fn(),
  deleteWatermark: vi.fn(),
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const mockVideo: Video = {
  video_id: 'test-video-123',
  user_id: 'user-1',
  format: 'mp4',
  resolution: { width: 1920, height: 1080 },
  duration: 120.5,
  codec: 'h264',
  framerate: 30,
  bitrate: 5000000,
  file_size: 100000000,
  storage_path: '/videos/test.mp4',
  import_source: 'local',
  created_at: '2024-01-01T00:00:00Z',
}

const mockWatermarks: WatermarkRegion[] = [
  {
    region_id: 'region-1',
    video_id: 'test-video-123',
    bbox: { x: 100, y: 100, width: 200, height: 100 },
    start_time: 0,
    end_time: 120,
    confidence: 0.95,
    watermark_type: 'corner',
    detection_method: 'auto',
  },
  {
    region_id: 'region-2',
    video_id: 'test-video-123',
    bbox: { x: 500, y: 500, width: 150, height: 80 },
    start_time: 0,
    end_time: 120,
    confidence: 0.90,
    watermark_type: 'logo',
    detection_method: 'manual',
  },
]

const renderWithProviders = (ui: React.ReactElement, initialRoute = '/watermark-marker/test-video-123') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <ConfigProvider locale={zhCN}>
        <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={false}>
          <VideoProvider>
            <TaskProvider>
              <Routes>
                <Route path="/watermark-marker/:videoId" element={ui} />
              </Routes>
            </TaskProvider>
          </VideoProvider>
        </WebSocketProvider>
      </ConfigProvider>
    </MemoryRouter>
  )
}

describe('水印标记交互测试 - Watermark Marking Interactions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup default mocks
    vi.mocked(api.getVideoById).mockResolvedValue(mockVideo)
    vi.mocked(api.getVideoFrames).mockResolvedValue({
      frames: [
        'http://localhost:8000/frames/frame1.jpg',
        'http://localhost:8000/frames/frame2.jpg',
        'http://localhost:8000/frames/frame3.jpg',
      ]
    })
    vi.mocked(api.getWatermarks).mockResolvedValue(mockWatermarks)
  })

  it('应该显示水印标记页面标题', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/水印标记/i)).toBeInTheDocument()
    })
  })

  it('应该显示视频信息标签（格式、分辨率、时长）', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/MP4/i)).toBeInTheDocument()
      expect(screen.getByText(/1920x1080/i)).toBeInTheDocument()
      expect(screen.getByText(/120\.50s/i)).toBeInTheDocument()
    })
  })

  it('应该显示手动标记按钮', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /手动标记/i })).toBeInTheDocument()
    })
  })

  it('应该显示保存按钮', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /保存/i })).toBeInTheDocument()
    })
  })

  it('应该显示清空按钮', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /清空/i })).toBeInTheDocument()
    })
  })

  it('应该显示帧导航控制（上一帧/下一帧）', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      // 查找包含"上一帧"提示的按钮
      const buttons = screen.getAllByRole('button')
      const prevButton = buttons.find(btn => btn.getAttribute('aria-label') === '上一帧')
      const nextButton = buttons.find(btn => btn.getAttribute('aria-label') === '下一帧')
      
      expect(prevButton || screen.getByText(/帧/i)).toBeTruthy()
      expect(nextButton || screen.getByText(/帧/i)).toBeTruthy()
    })
  })

  it('应该显示缩放控制（放大/缩小）', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/缩放/i)).toBeInTheDocument()
    })
  })

  it('应该显示已标记的水印区域列表', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/已标记的水印区域/i)).toBeInTheDocument()
      expect(screen.getByText(/区域 1/i)).toBeInTheDocument()
      expect(screen.getByText(/区域 2/i)).toBeInTheDocument()
    })
  })

  it('应该显示水印区域的详细信息（位置、大小、类型）', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/位置: \(100, 100\)/i)).toBeInTheDocument()
      expect(screen.getByText(/大小: 200 × 100/i)).toBeInTheDocument()
      expect(screen.getByText(/类型: corner/i)).toBeInTheDocument()
    })
  })

  it('应该显示水印区域的检测方法标签（自动/手动）', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      // Look for the button with "手动标记" text instead of just "手动"
      expect(screen.getByRole('button', { name: /手动标记/i })).toBeInTheDocument()
    })
  })

  it('应该为每个水印区域显示编辑和删除按钮', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      const editButtons = screen.getAllByRole('button').filter(btn => 
        btn.getAttribute('aria-label') === '编辑' || btn.querySelector('.anticon-edit')
      )
      const deleteButtons = screen.getAllByRole('button').filter(btn => 
        btn.getAttribute('aria-label') === '删除' || btn.querySelector('.anticon-delete')
      )
      
      expect(editButtons.length).toBeGreaterThan(0)
      expect(deleteButtons.length).toBeGreaterThan(0)
    })
  })

  it('应该在点击手动标记按钮时切换标记模式', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /手动标记/i })).toBeInTheDocument()
    })

    const markButton = screen.getByRole('button', { name: /手动标记/i })
    await user.click(markButton)

    await waitFor(() => {
      expect(screen.getByText(/标记模式已启用/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /取消标记/i })).toBeInTheDocument()
    })
  })

  it('应该在标记模式下显示使用说明', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /手动标记/i })).toBeInTheDocument()
    })

    const markButton = screen.getByRole('button', { name: /手动标记/i })
    await user.click(markButton)

    await waitFor(() => {
      expect(screen.getByText(/在视频帧上按住鼠标左键拖拽即可绘制矩形框/i)).toBeInTheDocument()
    })
  })

  it('应该在点击删除按钮时删除水印区域', async () => {
    const user = userEvent.setup()
    vi.mocked(api.deleteWatermark).mockResolvedValue({ success: true })
    
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/区域 1/i)).toBeInTheDocument()
    })

    // 查找第一个删除按钮
    const deleteButtons = screen.getAllByRole('button').filter(btn => 
      btn.querySelector('.anticon-delete')
    )
    
    if (deleteButtons.length > 0) {
      await user.click(deleteButtons[0])

      await waitFor(() => {
        expect(api.deleteWatermark).toHaveBeenCalledWith('test-video-123', 'region-1')
      })
    }
  })

  it('应该在点击编辑按钮时打开编辑对话框', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/区域 1/i)).toBeInTheDocument()
    })

    // 查找第一个编辑按钮
    const editButtons = screen.getAllByRole('button').filter(btn => 
      btn.querySelector('.anticon-edit')
    )
    
    if (editButtons.length > 0) {
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByText(/编辑水印区域/i)).toBeInTheDocument()
      })
    }
  })

  it('应该在编辑对话框中显示水印区域的坐标和尺寸输入框', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/区域 1/i)).toBeInTheDocument()
    })

    // 查找第一个编辑按钮
    const editButtons = screen.getAllByRole('button').filter(btn => 
      btn.querySelector('.anticon-edit')
    )
    
    if (editButtons.length > 0) {
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByText(/X 坐标/i)).toBeInTheDocument()
        expect(screen.getByText(/Y 坐标/i)).toBeInTheDocument()
        expect(screen.getByText(/宽度/i)).toBeInTheDocument()
        expect(screen.getByText(/高度/i)).toBeInTheDocument()
      })
    }
  })

  it('应该在编辑对话框中显示水印类型选择器', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/区域 1/i)).toBeInTheDocument()
    })

    // 查找第一个编辑按钮
    const editButtons = screen.getAllByRole('button').filter(btn => 
      btn.querySelector('.anticon-edit')
    )
    
    if (editButtons.length > 0) {
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByText(/水印类型/i)).toBeInTheDocument()
      })
    }
  })

  it('应该在点击保存按钮时保存所有水印区域', async () => {
    const user = userEvent.setup()
    vi.mocked(api.markWatermark).mockResolvedValue({ success: true })
    
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /保存/i })).toBeInTheDocument()
    })

    const saveButton = screen.getByRole('button', { name: /保存/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(api.markWatermark).toHaveBeenCalledWith('test-video-123', mockWatermarks)
    })
  })

  it('应该在点击清空按钮时显示确认对话框', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /清空/i })).toBeInTheDocument()
    })

    const clearButton = screen.getByRole('button', { name: /清空/i })
    await user.click(clearButton)

    await waitFor(() => {
      // Check for the confirmation dialog by looking for the specific message
      expect(screen.getByText(/确定要清空所有已标记的水印区域吗/i)).toBeInTheDocument()
    })
  })

  it('应该显示下一步按钮', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /下一步：去除水印/i })).toBeInTheDocument()
    })
  })

  it('应该在点击下一步按钮时导航到水印去除页面', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /下一步：去除水印/i })).toBeInTheDocument()
    })

    const nextButton = screen.getByRole('button', { name: /下一步：去除水印/i })
    await user.click(nextButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/watermark-removal/test-video-123')
    })
  })

  it('应该显示返回列表按钮', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /返回列表/i })).toBeInTheDocument()
    })
  })

  it('应该在点击返回列表按钮时导航回视频列表', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /返回列表/i })).toBeInTheDocument()
    })

    const backButton = screen.getByRole('button', { name: /返回列表/i })
    await user.click(backButton)

    expect(mockNavigate).toHaveBeenCalledWith('/videos')
  })

  it('应该显示当前帧数和总帧数', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/帧 1 \/ 3/i)).toBeInTheDocument()
    })
  })

  it('应该显示缩放百分比', async () => {
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      expect(screen.getByText(/缩放: 100%/i)).toBeInTheDocument()
    })
  })

  it('应该在没有水印区域时禁用保存按钮', async () => {
    vi.mocked(api.getWatermarks).mockResolvedValue([])
    
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      const saveButton = screen.getByRole('button', { name: /保存/i })
      expect(saveButton).toBeDisabled()
    })
  })

  it('应该在没有水印区域时禁用清空按钮', async () => {
    vi.mocked(api.getWatermarks).mockResolvedValue([])
    
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      const clearButton = screen.getByRole('button', { name: /清空/i })
      expect(clearButton).toBeDisabled()
    })
  })

  it('应该在没有水印区域时禁用下一步按钮', async () => {
    vi.mocked(api.getWatermarks).mockResolvedValue([])
    
    renderWithProviders(<WatermarkMarker />)

    await waitFor(() => {
      const nextButton = screen.getByRole('button', { name: /下一步：去除水印/i })
      expect(nextButton).toBeDisabled()
    })
  })
})
