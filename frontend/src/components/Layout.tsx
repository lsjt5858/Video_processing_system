import { useState } from 'react'
import { Layout as AntLayout, Menu, Typography } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  VideoCameraOutlined,
  UploadOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content, Footer } = AntLayout
const { Title } = Typography

/**
 * 应用布局组件
 * 包含侧边栏导航和主内容区域
 */
const Layout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    {
      key: '/videos',
      icon: <VideoCameraOutlined />,
      label: '视频列表',
    },
    {
      key: '/upload',
      icon: <UploadOutlined />,
      label: '上传',
    },
    {
      key: '/batch-processing',
      icon: <AppstoreOutlined />,
      label: '批处理',
    },
    {
      key: '/task-manager',
      icon: <UnorderedListOutlined />,
      label: '任务中心',
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  // 获取当前选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname
    if (path === '/') return '/videos'
    if (path.startsWith('/watermark-marker') || path.startsWith('/watermark-removal')) {
      return '/videos'
    }
    return path
  }

  return (
    <AntLayout style={{ minHeight: '100vh', height: '100vh', overflow: 'hidden' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        theme="dark"
        width={220}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          fontSize: collapsed ? '18px' : '20px',
          fontWeight: 'bold',
          padding: '0 16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          background: 'rgba(0, 0, 0, 0.2)',
        }}>
          {collapsed ? '一键美' : '一键美'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>
      
      <AntLayout style={{ marginLeft: collapsed ? 80 : 220, transition: 'margin-left 0.2s' }}>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          position: 'sticky',
          top: 0,
          zIndex: 10,
          height: 64,
        }}>
          <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
            一键美 - 智能视频处理平台
          </Title>
        </Header>
        
        <Content style={{ 
          margin: '16px',
          padding: '20px',
          background: '#f0f2f5',
          overflow: 'auto',
          height: 'calc(100vh - 64px - 48px)', // 减去 header 和 footer 高度
        }}>
          <div style={{ 
            maxWidth: '1400px', 
            margin: '0 auto',
            minHeight: '100%',
          }}>
            <Outlet />
          </div>
        </Content>
        
        <Footer style={{ 
          textAlign: 'center', 
          background: '#fff',
          padding: '12px 24px',
          borderTop: '1px solid #f0f0f0',
          fontSize: '13px',
          color: '#666',
        }}>
          一键美 ©2024 - 让视频更美好
        </Footer>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
