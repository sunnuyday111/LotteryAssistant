import { useEffect, useState } from 'react'
import {
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  Result,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import { CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useNavigate, useParams } from 'react-router-dom'
import { drawApi } from '@/api'
import { extractError } from '@/api/http'
import type { ClaimInfo, ClaimResult } from '@/types'

export default function ClaimPage() {
  const { eventId, recordId, code } = useParams<{
    eventId: string
    recordId: string
    code: string
  }>()
  const navigate = useNavigate()

  const evId = Number(eventId)
  const recId = Number(recordId)
  const valid = !!code && !Number.isNaN(evId) && !Number.isNaN(recId)

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [preview, setPreview] = useState<ClaimInfo | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [result, setResult] = useState<ClaimResult | null>(null)
  const [form] = Form.useForm<{ phone: string }>()

  useEffect(() => {
    if (!valid || !code) return
    setLoading(true)
    drawApi
      .claimPreview(evId, recId, code)
      .then((res) => {
        // 已领取时后端返回 success=false，但凭证本身有效，仍需展示中奖信息
        if (res.info) {
          setPreview(res.info)
          setPreviewError(res.success ? null : res.message)
        } else {
          setPreviewError(res.message)
        }
      })
      .catch((err) => setPreviewError(extractError(err)))
      .finally(() => setLoading(false))
  }, [code, evId, recId, valid])

  const handleClaim = async (values: { phone?: string }) => {
    if (!code) return
    setSubmitting(true)
    try {
      const res = await drawApi.claim(evId, recId, { code, phone: values?.phone })
      setResult(res)
    } catch (err) {
      message.error(extractError(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (!valid) {
    return (
      <div className="checkin-page">
        <Card className="checkin-card">
          <Result status="error" title="领奖链接无效" subTitle="缺少领奖码参数" />
        </Card>
      </div>
    )
  }

  if (result) {
    return (
      <div className="checkin-page">
        <Card className="checkin-card">
          <Result
            status={result.success ? 'success' : 'error'}
            icon={
              result.success ? (
                <CheckCircleFilled style={{ color: '#52c41a', fontSize: 72 }} />
              ) : (
                <CloseCircleFilled style={{ color: '#ff4d4f', fontSize: 72 }} />
              )
            }
            title={
              result.success
                ? '领奖成功'
                : result.already_claimed
                  ? '奖品已被领取'
                  : '领奖失败'
            }
            subTitle={result.message}
            extra={
              <Space direction="vertical" align="center">
                {result.info && (
                  <Descriptions
                    column={1}
                    size="small"
                    bordered
                    style={{ textAlign: 'left', minWidth: 280 }}
                  >
                    <Descriptions.Item label="中奖人">
                      {result.info.participant_name}
                    </Descriptions.Item>
                    <Descriptions.Item label="奖品">
                      {result.info.prize_name}
                    </Descriptions.Item>
                    <Descriptions.Item label="中奖时间">
                      {dayjs(result.info.drawn_at).format('YYYY-MM-DD HH:mm:ss')}
                    </Descriptions.Item>
                  </Descriptions>
                )}
                <Space>
                  <Button type="primary" onClick={() => navigate('/')}>
                    返回首页
                  </Button>
                  {result.success && (
                    <Button onClick={() => window.location.reload()}>
                      继续扫码领奖
                    </Button>
                  )}
                </Space>
              </Space>
            }
          />
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="checkin-page">
        <Card className="checkin-card">
          <Spin size="large" />
          <Typography.Paragraph type="secondary" style={{ marginTop: 16 }}>
            正在校验领奖凭证…
          </Typography.Paragraph>
        </Card>
      </div>
    )
  }

  if (previewError && !preview) {
    return (
      <div className="checkin-page">
        <Card className="checkin-card">
          <Result
            status="error"
            title={previewError}
            extra={
              <Button type="primary" onClick={() => navigate('/')}>
                返回首页
              </Button>
            }
          />
        </Card>
      </div>
    )
  }

  if (!preview) {
    return (
      <div className="checkin-page">
        <Card className="checkin-card">
          <Result
            status="error"
            title="领奖凭证无效"
            extra={
              <Button type="primary" onClick={() => navigate('/')}>
                返回首页
              </Button>
            }
          />
        </Card>
      </div>
    )
  }

  const alreadyClaimed = preview.claim_status === 'claimed'

  return (
    <div className="checkin-page">
      <Card className="checkin-card">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Typography.Title level={3} style={{ marginBottom: 8 }}>
              恭喜中奖
            </Typography.Title>
            <Tag color={alreadyClaimed ? 'default' : 'gold'} style={{ fontSize: 14 }}>
              {preview.prize_name}
            </Tag>
          </div>

          <Descriptions
            column={1}
            size="small"
            bordered
            items={[
              { key: 'name', label: '中奖人', children: preview.participant_name },
              {
                key: 'time',
                label: '中奖时间',
                children: dayjs(preview.drawn_at).format('YYYY-MM-DD HH:mm:ss'),
              },
              {
                key: 'status',
                label: '领取状态',
                children: alreadyClaimed ? (
                  <Tag color="success">
                    已领取 · {dayjs(preview.claimed_at).format('HH:mm:ss')}
                  </Tag>
                ) : (
                  <Tag color="warning">待领取</Tag>
                ),
              },
            ]}
          />

          {!alreadyClaimed && (
            <Form form={form} layout="vertical" onFinish={handleClaim}>
              <Form.Item
                name="phone"
                label="手机号后4位或完整手机号（用于核对身份）"
                rules={[
                  { required: true, message: '请输入手机号以确认领取' },
                  {
                    pattern: /^[\d]{4,11}$/,
                    message: '请输入至少 4 位数字（完整手机号或后4位）',
                  },
                ]}
              >
                <Input placeholder="例如 13800000001 或 0001" maxLength={11} />
              </Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                block
                size="large"
                loading={submitting}
              >
                确认领取奖品
              </Button>
            </Form>
          )}

          {alreadyClaimed && (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Typography.Text type="secondary" style={{ textAlign: 'center' }}>
                {previewError ?? '该奖品已核销，无需重复领取'}
              </Typography.Text>
              <Button block size="large" onClick={() => window.location.reload()}>
                重新扫码
              </Button>
            </Space>
          )}
        </Space>
      </Card>
    </div>
  )
}