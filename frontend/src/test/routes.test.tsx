import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import Layout from '@/components/Layout'
import VideoList from '@/pages/VideoList'
import VideoUpload from '@/pages/VideoUpload'
import WatermarkMarker from '@/pages/WatermarkMarker'
import WatermarkRemoval from '@/pages/WatermarkRemoval'
import BatchProcessing from '@/pages/BatchProcessing'
import TaskManager from '@/pages/TaskManager'
import { VideoProvider } from '@/contexts/VideoContext'
import { TaskProvider } from '@/contexts/TaskContext'
import { WebSocketProvider } from '@/contexts/WebSocketContext'

// Mock axios properly
vi.mock('axios', () => {
  const mockAxios = {
    create: vi.fn(() => mockAxios),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  }
  return { default: mockAxios }
})

// Helper to render with all providers
const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <ConfigProvider locale={zhCN}>
      <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={false}>
        <VideoProvider>
          <TaskProvider>
            {ui}
          </TaskProvider>
        </VideoProvider>
      </WebSocketProvider>
    </ConfigProvider>
  )
}

describe('路由测试 - Route Testing', () => {
  it('应该渲染根路径 / 并显示视频列表页面', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <Layout />,
          children: [
            {
              index: true,
              element: <VideoList />,
            },
          ],
        },
      ],
      {
        initialEntries: ['/'],
      }
    )

    renderWithProviders(<RouterProvider router={router} />)

    await waitFor(() => {
      // Look for the page title in the card header, not the menu
      const cardTitle = screen.getAllByText(/视频列表|Video List/i).find(el => 
        el.tagName === 'SPAN' && el.closest('.ant-card-head')
      )
      expect(cardTitle).toBeInTheDocument()
    })
  })

  it('应该渲染 /videos 路径并显示视频列表页面', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <Layout />,
          children: [
            {
              path: 'videos',
              element: <VideoList />,
            },
          ],
        },
      ],
      {
        initialEntries: ['/videos'],
      }
    )

    renderWithProviders(<RouterProvider router={router} />)

    await waitFor(() => {
      // Look for the page title in the card header
      const cardTitle = screen.getAllByText(/视频列表|Video List/i).find(el => 
        el.tagName === 'SPAN' && el.closest('.ant-card-head')
      )
      expect(cardTitle).toBeInTheDocument()
    })
  })

  it('应该渲染 /upload 路径并显示视频上传页面', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <Layout />,
          children: [
            {
              path: 'upload',
              element: <VideoUpload />,
            },
          ],
        },
      ],
      {
        initialEntries: ['/upload'],
      }
    )

    renderWithProviders(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText(/视频上传|上传视频|Video Upload/i)).toBeInTheDocument()
    })
  })

  it('应该渲染 /watermark-marker/:videoId 路径并显示水印标记页面', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <Layout />,
          children: [
            {
              path: 'watermark-marker/:videoId',
              element: <WatermarkMarker />,
            },
          ],
        },
      ],
      {
        initialEntries: ['/watermark-marker/test-video-123'],
      }
    )

    renderWithProviders(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText(/水印标记|Watermark Marker/i)).toBeInTheDocument()
    })
  })

  it('应该渲染 /watermark-removal/:videoId 路径并显示水印去除页面', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <Layout />,
          children: [
            {
              path: 'watermark-removal/:videoId',
              element: <WatermarkRemoval />,
            },
          ],
        },
      ],
      {
        initialEntries: ['/watermark-removal/test-video-123'],
      }
    )

    renderWithProviders(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText(/水印去除|Watermark Removal/i)).toBeInTheDocument()
    })
  })

  it('应该渲染 /batch-processing 路径并显示批量处理页面', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <Layout />,
          children: [
            {
              path: 'batch-processing',
              element: <BatchProcessing />,
            },
          ],
        },
      ],
      {
        initialEntries: ['/batch-processing'],
      }
    )

    renderWithProviders(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText(/批量处理|Batch Processing/i)).toBeInTheDocument()
    })
  })

  it('应该渲染 /task-manager 路径并显示任务管理页面', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <Layout />,
          children: [
            {
              path: 'task-manager',
              element: <TaskManager />,
            },
          ],
        },
      ],
      {
        initialEntries: ['/task-manager'],
      }
    )

    renderWithProviders(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText(/任务管理|Task Manager/i)).toBeInTheDocument()
    })
  })
})
