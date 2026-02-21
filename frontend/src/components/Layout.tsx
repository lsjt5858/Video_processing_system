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
    <AntLayout style={{ minHeight: '100vh', height: '100vh', overflow: 'hidden', background: 'transparent' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        width={240}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          boxShadow: '4px 0 24px rgba(0, 0, 0, 0.02)',
          borderRight: '1px solid var(--border-light)',
          zIndex: 20,
          background: 'rgba(255, 255, 255, 0.5)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
        }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--primary-color)',
          fontSize: collapsed ? '18px' : '22px',
          fontWeight: 800,
          padding: '0 16px',
          borderBottom: '1px solid rgba(0, 0, 0, 0.04)',
          background: 'transparent',
          letterSpacing: '0.5px',
        }}>
          {collapsed ? '一键美' : '✨ 一键美'}
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0, background: 'transparent' }}
        />
      </Sider>

      <AntLayout style={{ marginLeft: collapsed ? 80 : 240, transition: 'margin-left 0.2s cubic-bezier(0.2, 0, 0, 1)', background: 'transparent' }}>
        <Header style={{
          background: 'rgba(255, 255, 255, 0.7)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          padding: '0 32px',
          display: 'flex',
          alignItems: 'center',
          boxShadow: '0 4px 24px -8px rgba(0,0,0,0.05)',
          position: 'sticky',
          top: 0,
          zIndex: 10,
          height: 64,
          borderBottom: '1px solid rgba(255, 255, 255, 0.6)',
        }}>
          <Title level={4} className="gradient-text" style={{ margin: 0, fontWeight: 700 }}>
            智能视频处理平台
          </Title>
        </Header>

        <Content style={{
          margin: '0',
          padding: '24px 32px',
          background: 'transparent',
          overflow: 'auto',
          height: 'calc(100vh - 64px - 48px)', // 减去 header 和 footer 高度
          position: 'relative'
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
          background: 'transparent',
          padding: '12px 24px',
          fontSize: '13px',
          color: 'var(--text-tertiary)',
        }}>
          ✨ 一键美 ©2024 - 打造极致视频体验
        </Footer>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
