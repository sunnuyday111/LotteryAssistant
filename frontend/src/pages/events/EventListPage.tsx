import { useEffect, useState } from 'react'
import {
  Button,
  Card,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { eventApi } from '@/api'
import { extractError } from '@/api/http'
import { openLotteryScreen } from '@/utils/openLottery'
import type { EventCreatePayload, EventItem, EventStatus } from '@/types'

const STATUS_META: Record<EventStatus, { text: string; color: string }> = {
  draft: { text: '草稿', color: 'default' },
  ongoing: { text: '进行中', color: 'processing' },
  finished: { text: '已结束', color: 'success' },
}

export default function EventListPage() {
  const [events, setEvents] = useState<EventItem[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form] = Form.useForm<EventCreatePayload>()
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    try {
      setEvents(await eventApi.list())
    } catch (err) {
      message.error(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      const created = await eventApi.create(values)
      message.success('活动创建成功')
      setModalOpen(false)
      form.resetFields()
      navigate(`/events/${created.id}`)
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error(extractError(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await eventApi.remove(id)
      message.success('已删除')
      void load()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  return (
    <Card
      title="活动管理"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void load()}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
          >
            新建活动
          </Button>
        </Space>
      }
    >
      <Table<EventItem>
        rowKey="id"
        loading={loading}
        dataSource={events}
        locale={{ emptyText: <Empty description="暂无活动，点击右上角新建" /> }}
        columns={[
          {
            title: '活动名称',
            dataIndex: 'name',
            render: (name: string, record) => (
              <Typography.Link onClick={() => navigate(`/events/${record.id}`)}>
                {name}
              </Typography.Link>
            ),
          },
          {
            title: '地点',
            dataIndex: 'location',
            render: (v: string | null) => v || '-',
          },
          {
            title: '开始时间',
            dataIndex: 'start_time',
            render: (v: string | null) =>
              v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-',
          },
          {
            title: '状态',
            dataIndex: 'status',
            render: (status: EventStatus) => (
              <Tag color={STATUS_META[status].color}>
                {STATUS_META[status].text}
              </Tag>
            ),
          },
          {
            title: '操作',
            width: 240,
            render: (_, record) => (
              <Space>
                <Button
                  size="small"
                  onClick={() => navigate(`/events/${record.id}`)}
                >
                  管理
                </Button>
                <Button
                  size="small"
                  onClick={() => navigate(`/events/${record.id}/dashboard`)}
                >
                  看板
                </Button>
                <Button
                  size="small"
                  onClick={() => void openLotteryScreen(record.id)}
                >
                  大屏
                </Button>
                <Popconfirm
                  title="确认删除该活动？"
                  description="将同时删除名单、签到与中奖记录"
                  onConfirm={() => handleDelete(record.id)}
                >
                  <Button size="small" danger>
                    删除
                  </Button>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title="新建活动"
        open={modalOpen}
        onOk={handleCreate}
        confirmLoading={submitting}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item
            name="name"
            label="活动名称"
            rules={[{ required: true, message: '请输入活动名称' }]}
          >
            <Input placeholder="例如：2026 公司年会" maxLength={200} />
          </Form.Item>
          <Form.Item name="location" label="活动地点">
            <Input placeholder="例如：三楼宴会厅" maxLength={200} />
          </Form.Item>
          <Form.Item name="description" label="活动说明">
            <Input.TextArea rows={3} placeholder="活动简介、注意事项等" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
