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
      label: '上传视频',
    },
    {
      key: '/batch-processing',
      icon: <AppstoreOutlined />,
      label: '批量处理',
    },
    {
      key: '/task-manager',
      icon: <UnorderedListOutlined />,
      label: '任务管理',
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
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        theme="dark"
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          fontSize: collapsed ? '16px' : '18px',
          fontWeight: 'bold',
          padding: '0 16px'
        }}>
          {collapsed ? '视频' : '视频再创作平台'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      
      <AntLayout>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <Title level={4} style={{ margin: 0 }}>
            视频再创作智能处理平台
          </Title>
        </Header>
        
        <Content style={{ margin: '24px 16px', padding: 24, background: '#f0f2f5' }}>
          <Outlet />
        </Content>
        
        <Footer style={{ textAlign: 'center', background: '#fff' }}>
          视频再创作智能处理平台 ©2024
        </Footer>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
