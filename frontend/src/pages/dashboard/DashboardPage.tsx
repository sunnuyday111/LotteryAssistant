import { useCallback, useEffect, useState } from 'react'
import {
  Button,
  Card,
  Col,
  Empty,
  Progress,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { exportApi, statsApi } from '@/api'
import { extractError } from '@/api/http'
import { isTauri } from '@/utils/isTauri'
import { invoke } from '@/utils/tauriInvoke'
import type { EventStats, PrizeStat } from '@/types'

export default function DashboardPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const id = Number(eventId)
  const navigate = useNavigate()

  const [stats, setStats] = useState<EventStats | null>(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    if (!id) return
    setLoading(true)
    try {
      setStats(await statsApi.get(id))
    } catch (err) {
      message.error(extractError(err))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const downloadBlob = async (blob: Blob, filename: string) => {
    if (isTauri()) {
      const buf = await blob.arrayBuffer()
      const bytes = new Uint8Array(buf)
      let binary = ''
      for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i])
      const dataBase64 = btoa(binary)
      try {
        await invoke('save_download', { filename, dataBase64 })
        message.success(`已保存到下载文件夹：${filename}`)
      } catch (err) {
        message.error(`保存失败：${String(err)}`)
      }
      return
    }
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleExportCheckins = async () => {
    try {
      const res = await exportApi.checkins(id)
      await downloadBlob(res.data, `${stats?.event_name ?? '活动'}_签到明细.xlsx`)
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const handleExportDraws = async () => {
    try {
      const res = await exportApi.draws(id)
      await downloadBlob(res.data, `${stats?.event_name ?? '活动'}_中奖名单.xlsx`)
    } catch (err) {
      message.error(extractError(err))
    }
  }

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card
        title={`数据看板 · ${stats?.event_name ?? ''}`}
        loading={loading && !stats}
        extra={
          <Space>
            <Button onClick={() => navigate(`/events/${id}`)}>返回活动</Button>
            <Button icon={<ReloadOutlined />} onClick={() => void load()}>
              刷新
            </Button>
          </Space>
        }
      >
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="总人数" value={stats?.total_participants ?? 0} />
          </Col>
          <Col span={6}>
            <Statistic
              title="已签到"
              value={stats?.checked_in ?? 0}
              valueStyle={{ color: '#16a34a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="未签到"
              value={stats?.not_checked_in ?? 0}
              valueStyle={{ color: '#dc2626' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="签到率"
              value={((stats?.checkin_rate ?? 0) * 100).toFixed(1)}
              suffix="%"
              valueStyle={{ color: '#6d28d9' }}
            />
          </Col>
        </Row>
        <Progress
          style={{ marginTop: 16 }}
          percent={Number(((stats?.checkin_rate ?? 0) * 100).toFixed(1))}
          status="active"
        />
        <Row gutter={16} style={{ marginTop: 24 }}>
          <Col span={8}>
            <Statistic
              title="待领取"
              value={stats?.claim_pending ?? 0}
              valueStyle={{ color: '#d97706' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="已领取"
              value={stats?.claim_claimed ?? 0}
              valueStyle={{ color: '#16a34a' }}
            />
          </Col>
          <Col span={8}>
            <Statistic title="免领奖项" value={stats?.claim_exempt ?? 0} />
          </Col>
        </Row>
      </Card>

      <Card
        title="各奖项中奖情况"
        extra={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExportCheckins}>
              导出签到明细
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExportDraws}>
              导出中奖名单
            </Button>
          </Space>
        }
      >
        <Table<PrizeStat>
          rowKey="prize_id"
          dataSource={stats?.prize_stats ?? []}
          pagination={false}
          locale={{ emptyText: <Empty description="暂无奖项" /> }}
          columns={[
            { title: '奖项名称', dataIndex: 'prize_name' },
            { title: '奖项数量', dataIndex: 'quantity', width: 100 },
            { title: '已中奖人数', dataIndex: 'drawn_count', width: 110 },
            {
              title: '领取方式',
              dataIndex: 'claim_required',
              width: 110,
              render: (v: boolean) =>
                v ? <Tag color="gold">现场扫码</Tag> : <Tag>免领</Tag>,
            },
            {
              title: '待领取',
              dataIndex: 'pending_count',
              width: 90,
              render: (v: number, r) =>
                r.claim_required ? (
                  <Typography.Text type="warning">{v}</Typography.Text>
                ) : (
                  '-'
                ),
            },
            {
              title: '已领取',
              dataIndex: 'claimed_count',
              width: 90,
              render: (v: number, r) =>
                r.claim_required ? (
                  <Typography.Text type="success">{v}</Typography.Text>
                ) : (
                  '-'
                ),
            },
            {
              title: '进度',
              render: (_, record) => (
                <Progress
                  percent={Number(
                    ((record.drawn_count / record.quantity) * 100).toFixed(0),
                  )}
                  size="small"
                />
              ),
            },
          ]}
        />
        <Typography.Text type="secondary" style={{ display: 'block', marginTop: 12 }}>
          提示：抽奖结果由后端随机生成并持久化，前端仅负责动画展示。
        </Typography.Text>
      </Card>
    </Space>
  )
}
