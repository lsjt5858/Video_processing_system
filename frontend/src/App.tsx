import { ConfigProvider } from 'antd'
import { RouterProvider } from 'react-router-dom'
import zhCN from 'antd/locale/zh_CN'
import router from './router'
import { VideoProvider } from './contexts/VideoContext'
import { TaskProvider } from './contexts/TaskContext'
import { WebSocketProvider } from './contexts/WebSocketContext'
import './App.css'

/**
 * 应用根组件
 * 配置全局主题、状态管理和路由
 */
function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <WebSocketProvider 
        url="ws://localhost:8000/ws"
        autoConnect={true}
        reconnectInterval={3000}
        maxReconnectAttempts={10}
      >
        <VideoProvider>
          <TaskProvider>
            <RouterProvider router={router} />
          </TaskProvider>
        </VideoProvider>
      </WebSocketProvider>
    </ConfigProvider>
  )
}

export default App
