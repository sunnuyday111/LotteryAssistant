/** 解锁页：输入管理口令后才能进入后台与大屏。
 *
 *  校验方式是直接打一个受保护接口：口令正确会拿到数据并放行，
 *  错误则由响应拦截器清空口令，这里只需给出可读的错误提示。
 */

import { useState } from 'react'
import { Alert, Button, Card, Input, Space, Typography } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import { eventApi } from '@/api'
import { extractError } from '@/api/http'
import { clearAdminToken, setAdminToken } from '@/api/adminAuth'

const { Title, Paragraph, Text } = Typography

export default function UnlockPage() {
  const [value, setValue] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleUnlock = async () => {
    const token = value.trim()
    if (!token) {
      setError('请输入管理口令')
      return
    }

    setLoading(true)
    setError('')
    // 先写入再校验：后续请求的拦截器才会带上这个口令
    setAdminToken(token)

    try {
      await eventApi.list()
    } catch (err) {
      // 拦截器已清空口令，这里只负责给出可读提示
      clearAdminToken()
      setError(extractError(err))
      setValue('')
      setLoading(false)
      return
    }

    // 成功：由 useSyncExternalStore 触发路由重渲染，无需手动跳转
    setLoading(false)
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(160deg, #f5f3ff 0%, #ede9fe 100%)',
        padding: 24,
      }}
    >
      <Card style={{ width: 420, boxShadow: '0 12px 40px rgba(109, 40, 217, 0.12)' }}>
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <Title level={4} style={{ margin: 0 }}>
            <LockOutlined style={{ marginRight: 8 }} />
            活动签到抽奖助手
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 16 }}>
            请输入管理口令以继续
          </Paragraph>

          {error && (
            <Alert
              type="error"
              showIcon
              message={error}
              style={{ marginBottom: 16 }}
              closable
              onClose={() => setError('')}
            />
          )}

          <Input.Password
            size="large"
            autoFocus
            placeholder="管理口令"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onPressEnter={() => void handleUnlock()}
          />
          <Button
            type="primary"
            size="large"
            block
            loading={loading}
            onClick={() => void handleUnlock()}
          >
            解锁
          </Button>

          <Text type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
            口令在启动后端时打印于控制台，也可通过环境变量 ADMIN_TOKEN 配置。
            参与者扫码的签到页与领奖页无需口令。
          </Text>
        </Space>
      </Card>
    </div>
  )
}
