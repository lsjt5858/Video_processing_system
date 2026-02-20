import { createBrowserRouter } from 'react-router-dom'
import Layout from '@/components/Layout'
import VideoList from '@/pages/VideoList'
import VideoUpload from '@/pages/VideoUpload'
import WatermarkMarker from '@/pages/WatermarkMarker'
import WatermarkRemoval from '@/pages/WatermarkRemoval'
import BatchProcessing from '@/pages/BatchProcessing'
import TaskManager from '@/pages/TaskManager'

/**
 * 路由配置
 */
const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <VideoList />,
      },
      {
        path: 'videos',
        element: <VideoList />,
      },
      {
        path: 'upload',
        element: <VideoUpload />,
      },
      {
        path: 'watermark-marker/:videoId',
        element: <WatermarkMarker />,
      },
      {
        path: 'watermark-removal/:videoId',
        element: <WatermarkRemoval />,
      },
      {
        path: 'batch-processing',
        element: <BatchProcessing />,
      },
      {
        path: 'task-manager',
        element: <TaskManager />,
      },
    ],
  },
])

export default router
