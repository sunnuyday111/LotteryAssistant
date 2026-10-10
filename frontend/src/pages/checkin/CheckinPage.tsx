import { useEffect, useState } from 'react'
import { Button, Form, Input, Result, Spin, Typography, message } from 'antd'
import { CheckCircleFilled } from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import { checkinApi } from '@/api'
import { extractError } from '@/api/http'
import type { CheckinEventInfo, CheckinResult } from '@/types'

export default function CheckinPage() {
  const { token } = useParams<{ token: string }>()
  const [info, setInfo] = useState<CheckinEventInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<CheckinResult | null>(null)
  const [form] = Form.useForm<{ name: string; phone: string }>()

  useEffect(() => {
    if (!token) return
    setLoading(true)
    checkinApi
      .info(token)
      .then(setInfo)
      .catch((err) => message.error(extractError(err)))
      .finally(() => setLoading(false))
  }, [token])

  const handleSubmit = async (values: { name: string; phone: string }) => {
    if (!token) return
    setSubmitting(true)
    try {
      const res = await checkinApi.submit(token, values)
      setResult(res)
    } catch (err) {
      message.error(extractError(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="checkin-page">
        <Spin size="large" />
      </div>
    )
  }

  if (!info) {
    return (
      <div className="checkin-page">
        <div className="checkin-card">
          <Result status="warning" title="签到链接无效或已失效" />
        </div>
      </div>
    )
  }

  return (
    <div className="checkin-page">
      <div className="checkin-card">
        {result ? (
          <Result
            status={result.success ? 'success' : 'error'}
            icon={result.success ? <CheckCircleFilled /> : undefined}
            title={result.success ? '签到成功' : '签到失败'}
            subTitle={result.message}
            extra={
              result.success && (
                <Typography.Text type="secondary">
                  {result.participant_name}，欢迎参加「{info.name}」
                </Typography.Text>
              )
            }
          />
        ) : (
          <>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Typography.Title level={3} style={{ marginBottom: 4 }}>
                {info.name}
              </Typography.Title>
              {info.location && (
                <Typography.Text type="secondary">{info.location}</Typography.Text>
              )}
              <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>
                请输入报名时登记的姓名和手机号完成签到
              </Typography.Paragraph>
            </div>
            <Form form={form} layout="vertical" onFinish={handleSubmit} size="large">
              <Form.Item
                name="name"
                label="姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input placeholder="请输入姓名" maxLength={100} />
              </Form.Item>
              <Form.Item
                name="phone"
                label="手机号"
                rules={[{ required: true, message: '请输入手机号' }]}
              >
                <Input placeholder="请输入手机号" maxLength={30} inputMode="tel" />
              </Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                block
                size="large"
                loading={submitting}
              >
                立即签到
              </Button>
            </Form>
          </>
        )}
      </div>
    </div>
  )
}
