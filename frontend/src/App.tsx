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
    <ConfigProvider 
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#6366f1',
          colorInfo: '#6366f1',
          colorSuccess: '#10b981',
          colorWarning: '#f59e0b',
          colorError: '#ef4444',
          borderRadius: 8,
          borderRadiusLG: 16,
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        },
        components: {
          Card: {
            borderRadiusLG: 16,
          },
          Button: {
            borderRadius: 8,
            controlHeight: 40,
          },
        }
      }}
    >
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
