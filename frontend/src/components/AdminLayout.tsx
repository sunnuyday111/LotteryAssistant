import { Layout, Menu, Typography } from 'antd'
import { GiftOutlined, UnorderedListOutlined } from '@ant-design/icons'
import { Link, Outlet, useLocation } from 'react-router-dom'

const { Header, Content, Sider } = Layout

export default function AdminLayout() {
  const location = useLocation()
  const selectedKey = location.pathname.startsWith('/events') ? 'events' : 'events'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: 'linear-gradient(90deg, #4c1d95, #6d28d9)',
          paddingInline: 24,
        }}
      >
        <GiftOutlined style={{ fontSize: 24, color: '#fbbf24', marginRight: 12 }} />
        <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
          活动签到抽奖助手
        </Typography.Title>
      </Header>
      <Layout>
        <Sider width={200} theme="light">
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            style={{ height: '100%', borderRight: 0 }}
            items={[
              {
                key: 'events',
                icon: <UnorderedListOutlined />,
                label: <Link to="/events">活动管理</Link>,
              },
            ]}
          />
        </Sider>
        <Content style={{ padding: 24, overflow: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
