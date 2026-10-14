import { useCallback, useEffect, useState } from 'react'
import {
  Button,
  Card,
  Descriptions,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload,
  Dropdown,
  message,
} from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  PauseCircleOutlined,
  PlusOutlined,
  QrcodeOutlined,
  UploadOutlined,
  UserAddOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { eventApi, exportApi, checkinApi, participantApi, prizeApi, drawApi } from '@/api'
import { extractError } from '@/api/http'
import { openLotteryScreen } from '@/utils/openLottery'
import { isTauri } from '@/utils/isTauri'
import { invoke } from '@/utils/tauriInvoke'
import type {
  ClaimStats,
  DrawRecord,
  EventDetail,
  Participant,
  ParticipantImportResult,
  Prize,
  PrizePayload,
} from '@/types'

/** 抽奖玩法中文名。 */
const DRAW_MODE_LABEL: Record<string, string> = {
  roll: '滚动名单',
  wheel: '轮盘转盘',
  egg: '砸金蛋',
  grid: '九宫格',
}

export default function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const id = Number(eventId)
  const navigate = useNavigate()

  const [event, setEvent] = useState<EventDetail | null>(null)
  const [participants, setParticipants] = useState<Participant[]>([])
  const [prizes, setPrizes] = useState<Prize[]>([])
  const [loading, setLoading] = useState(false)

  const [qrOpen, setQrOpen] = useState(false)
  const [checkinUrl, setCheckinUrl] = useState('')
  const [qrImage, setQrImage] = useState('')
  const [importResult, setImportResult] = useState<ParticipantImportResult | null>(
    null,
  )
  const [importOpen, setImportOpen] = useState(false)

  const [prizeModalOpen, setPrizeModalOpen] = useState(false)
  const [editingPrize, setEditingPrize] = useState<Prize | null>(null)
  const [prizeForm] = Form.useForm<PrizePayload>()

  // 中奖记录 / 领奖管理
  const [records, setRecords] = useState<DrawRecord[]>([])
  const [claimStats, setClaimStats] = useState<ClaimStats | null>(null)
  const [claimFilter, setClaimFilter] = useState<
    'all' | 'pending' | 'claimed' | 'exempt'
  >('all')
  const [claimQrOpen, setClaimQrOpen] = useState(false)
  const [claimQrImage, setClaimQrImage] = useState('')
  const [claimQrRecord, setClaimQrRecord] = useState<DrawRecord | null>(null)

  // 手动添加参与者
  const [addOpen, setAddOpen] = useState(false)
  const [addSubmitting, setAddSubmitting] = useState(false)
  const [addForm] = Form.useForm<{ name: string; phone: string; department?: string }>()

  const loadAll = useCallback(async () => {
    if (!id) return
    setLoading(true)
    try {
      const [detail, parts, prizeList, recs, cStats] = await Promise.all([
        eventApi.get(id),
        participantApi.list(id),
        prizeApi.list(id),
        drawApi.records(id),
        drawApi.claimStats(id),
      ])
      setEvent(detail)
      setParticipants(parts)
      setPrizes(prizeList)
      setRecords(recs)
      setClaimStats(cStats)
    } catch (err) {
      message.error(extractError(err))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  const showQrcode = async () => {
    try {
      const data = await eventApi.checkinUrl(id)
      setCheckinUrl(data.url)
      // Tauri WebView 用 <img src="/api/..."> 在 tauri:// 协议下加载不到，
      // 改为 axios 直接取 PNG 并转 data:URL 内嵌显示
      const res = await eventApi.qrcode(id)
      const blob = res.data as Blob
      const reader = new FileReader()
      reader.onload = () => setQrImage(String(reader.result))
      reader.readAsDataURL(blob)
      setQrOpen(true)
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const handleImport = async (file: File) => {
    try {
      const result = await participantApi.import(id, file)
      setImportResult(result)
      setImportOpen(true)
      void loadAll()
    } catch (err) {
      message.error(extractError(err))
    }
    return false
  }

  const handleDeleteParticipant = async (participantId: number) => {
    try {
      await participantApi.remove(id, participantId)
      message.success('已删除')
      void loadAll()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const openAddModal = () => {
    addForm.resetFields()
    setAddOpen(true)
  }

  const handleAddParticipant = async () => {
    try {
      const values = await addForm.validateFields()
      setAddSubmitting(true)
      await participantApi.create(id, {
        name: values.name,
        phone: values.phone,
        department: values.department,
      })
      message.success('已添加参与者')
      setAddOpen(false)
      void loadAll()
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error(extractError(err))
    } finally {
      setAddSubmitting(false)
    }
  }

  const handleManualCheckin = async (participantId: number) => {
    try {
      const result = await checkinApi.manual(id, participantId)
      message.success(result.message)
      void loadAll()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const handleCancelCheckin = async (participantId: number) => {
    try {
      await checkinApi.cancel(id, participantId)
      message.success('已取消签到')
      void loadAll()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const openPrizeModal = (prize?: Prize) => {
    setEditingPrize(prize ?? null)
    prizeForm.setFieldsValue(
      prize
        ? {
            name: prize.name,
            quantity: prize.quantity,
            sort_order: prize.sort_order,
            description: prize.description,
            draw_mode: prize.draw_mode ?? 'roll',
            claim_required: prize.claim_required ?? true,
          }
        : {
            name: '',
            quantity: 1,
            sort_order: prizes.length,
            description: '',
            draw_mode: 'roll',
            claim_required: true,
          },
    )
    setPrizeModalOpen(true)
  }

  const handleSavePrize = async () => {
    try {
      const values = await prizeForm.validateFields()
      if (editingPrize) {
        await prizeApi.update(id, editingPrize.id, values)
        message.success('奖项已更新')
      } else {
        await prizeApi.create(id, values)
        message.success('奖项已创建')
      }
      setPrizeModalOpen(false)
      void loadAll()
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error(extractError(err))
    }
  }

  const handleDeletePrize = async (prizeId: number) => {
    try {
      await prizeApi.remove(id, prizeId)
      message.success('已删除')
      void loadAll()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const handleChangeStatus = async (status: 'draft' | 'ongoing' | 'finished') => {
    try {
      await eventApi.update(id, { status })
      message.success(
        status === 'finished' ? '已结束活动' :
        status === 'ongoing' ? '已开启活动' : '已重置为草稿',
      )
      void loadAll()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  /** 展示某条中奖记录的领奖二维码。 */
  const showClaimQrcode = async (record: DrawRecord) => {
    setClaimQrRecord(record)
    setClaimQrOpen(true)
    try {
      const res = await drawApi.claimQrcode(id, record.id)
      const blob = res.data as Blob
      const reader = new FileReader()
      reader.onload = () => setClaimQrImage(String(reader.result))
      reader.readAsDataURL(blob)
    } catch (err) {
      message.error(extractError(err))
    }
  }

  /** 主办方手动核销领奖。 */
  const handleRevokeClaim = async (record: DrawRecord) => {
    try {
      await drawApi.revokeClaim(id, record.id)
      message.success('已撤销领奖，恢复为待领取')
      void loadAll()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  /** 主办方手动核销领奖（手机没电 / 二维码丢失时使用）。 */
  const handleManualClaim = async (record: DrawRecord) => {
    try {
      const res = await drawApi.manualClaim(id, record.id)
      if (res.success) {
        message.success(res.message)
      } else {
        message.warning(res.message)
      }
      void loadAll()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const downloadBlob = async (blob: Blob, filename: string) => {
    if (isTauri()) {
      // Tauri WebView 下 blob: URL 的 <a download> 不可靠，改用 Rust 端落盘
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
      await downloadBlob(res.data, `${event?.name ?? '活动'}_签到明细.xlsx`)
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const handleExportDraws = async () => {
    try {
      const res = await exportApi.draws(id)
      await downloadBlob(res.data, `${event?.name ?? '活动'}_中奖名单.xlsx`)
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const checkedCount = participants.filter((p) => p.checked_in).length

  /** 中奖记录按领取状态过滤。 */
  const filteredRecords = records.filter((r) => {
    if (claimFilter === 'all') return true
    if (claimFilter === 'exempt') return !r.claim_required
    if (claimFilter === 'pending') return r.claim_required && r.claim_status === 'pending'
    return r.claim_required && r.claim_status === 'claimed'
  })

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card
        loading={loading && !event}
        title={event?.name ?? '活动详情'}
        extra={
          <Space>
            <Button onClick={() => navigate('/events')}>返回列表</Button>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'draft',
                    icon: <ClockCircleOutlined />,
                    label: '重置为草稿',
                    disabled: event?.status === 'draft',
                  },
                  {
                    key: 'ongoing',
                    icon: <CheckCircleOutlined />,
                    label: '开启活动（进行中）',
                    disabled: event?.status === 'ongoing',
                  },
                  {
                    key: 'finished',
                    icon: <PauseCircleOutlined />,
                    label: '结束活动',
                    disabled: event?.status === 'finished',
                  },
                ],
                onClick: ({ key }) => {
                  void handleChangeStatus(
                    key as 'draft' | 'ongoing' | 'finished',
                  )
                },
              }}
            >
              <Button>切换状态</Button>
            </Dropdown>
            <Button
              type="primary"
              onClick={() => void openLotteryScreen(id)}
            >
              打开抽奖大屏
            </Button>
          </Space>
        }
      >
        {event && (
          <Descriptions column={3} size="small">
            <Descriptions.Item label="地点">
              {event.location || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="开始时间">
              {event.start_time
                ? dayjs(event.start_time).format('YYYY-MM-DD HH:mm')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color="processing">{event.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="总人数">
              {event.participant_count}
            </Descriptions.Item>
            <Descriptions.Item label="已签到">
              {event.checkin_count}
            </Descriptions.Item>
            <Descriptions.Item label="奖项数">
              {event.prize_count}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      <Card>
        <Tabs
          items={[
            {
              key: 'participants',
              label: `参与者名单 (${participants.length})`,
              children: (
                <>
                  <Space style={{ marginBottom: 16 }} wrap>
                    <Upload
                      accept=".xlsx,.xls,.csv"
                      showUploadList={false}
                      beforeUpload={(file) => handleImport(file)}
                    >
                      <Button icon={<UploadOutlined />}>导入 Excel/CSV</Button>
                    </Upload>
                    <Button icon={<UserAddOutlined />} onClick={openAddModal}>
                      添加参与者
                    </Button>
                    <Button icon={<QrcodeOutlined />} onClick={showQrcode}>
                      签到二维码
                    </Button>
                    <Button icon={<DownloadOutlined />} onClick={handleExportCheckins}>
                      导出签到明细
                    </Button>
                    <Typography.Text type="secondary">
                      已签到 {checkedCount} / {participants.length}
                    </Typography.Text>
                  </Space>
                  <Table<Participant>
                    rowKey="id"
                    size="small"
                    dataSource={participants}
                    locale={{ emptyText: <Empty description="暂无名单，请导入" /> }}
                    pagination={{ pageSize: 10, showSizeChanger: true }}
                    columns={[
                      { title: '姓名', dataIndex: 'name' },
                      { title: '手机号', dataIndex: 'phone' },
                      {
                        title: '部门',
                        dataIndex: 'department',
                        render: (v: string | null) => v || '-',
                      },
                      {
                        title: '签到状态',
                        dataIndex: 'checked_in',
                        render: (v: boolean) =>
                          v ? (
                            <Tag color="success">已签到</Tag>
                          ) : (
                            <Tag>未签到</Tag>
                          ),
                      },
                      {
                        title: '操作',
                        width: 180,
                        render: (_, record) => (
                          <Space>
                            {record.checked_in ? (
                              <Button
                                size="small"
                                onClick={() => handleCancelCheckin(record.id)}
                              >
                                取消签到
                              </Button>
                            ) : (
                              <Button
                                size="small"
                                type="link"
                                onClick={() => handleManualCheckin(record.id)}
                              >
                                手动签到
                              </Button>
                            )}
                            <Popconfirm
                              title="确认删除该参与者？"
                              onConfirm={() => handleDeleteParticipant(record.id)}
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
                </>
              ),
            },
            {
              key: 'prizes',
              label: `奖项配置 (${prizes.length})`,
              children: (
                <>
                  <Space style={{ marginBottom: 16 }}>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => openPrizeModal()}
                    >
                      新增奖项
                    </Button>
                    <Button icon={<DownloadOutlined />} onClick={handleExportDraws}>
                      导出中奖名单
                    </Button>
                  </Space>
                  <Table<Prize>
                    rowKey="id"
                    size="small"
                    dataSource={prizes}
                    locale={{ emptyText: <Empty description="暂无奖项" /> }}
                    pagination={false}
                    columns={[
                      { title: '奖项名称', dataIndex: 'name' },
                      { title: '数量', dataIndex: 'quantity', width: 80 },
                      {
                        title: '已抽取',
                        dataIndex: 'drawn_count',
                        width: 90,
                        render: (v: number, r) => `${v} / ${r.quantity}`,
                      },
                      {
                        title: '玩法',
                        dataIndex: 'draw_mode',
                        width: 100,
                        render: (v: string) => DRAW_MODE_LABEL[v] ?? v,
                      },
                      {
                        title: '领奖',
                        dataIndex: 'claim_required',
                        width: 90,
                        render: (v: boolean) =>
                          v ? <Tag color="gold">需扫码</Tag> : <Tag>免领</Tag>,
                      },
                      {
                        title: '排序',
                        dataIndex: 'sort_order',
                        width: 70,
                      },
                      {
                        title: '操作',
                        width: 160,
                        render: (_, record) => (
                          <Space>
                            <Button
                              size="small"
                              onClick={() => openPrizeModal(record)}
                            >
                              编辑
                            </Button>
                            <Popconfirm
                              title="确认删除该奖项？"
                              onConfirm={() => handleDeletePrize(record.id)}
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
                </>
              ),
            },
            {
              key: 'claims',
              label: `中奖与领奖 (${records.length})`,
              children: (
                <>
                  <Space style={{ marginBottom: 16 }} wrap>
                    <Tag color="warning">
                      待领取 {claimStats?.pending ?? 0}
                    </Tag>
                    <Tag color="success">
                      已领取 {claimStats?.claimed ?? 0}
                    </Tag>
                    <Tag>免领 {claimStats?.exempt ?? 0}</Tag>
                    <Select
                      style={{ width: 160 }}
                      value={claimFilter}
                      onChange={setClaimFilter}
                      options={[
                        { value: 'all', label: '全部记录' },
                        { value: 'pending', label: '仅待领取' },
                        { value: 'claimed', label: '仅已领取' },
                        { value: 'exempt', label: '仅免领奖项' },
                      ]}
                    />
                    <Button icon={<DownloadOutlined />} onClick={handleExportDraws}>
                      导出中奖名单
                    </Button>
                  </Space>
                  <Table<DrawRecord>
                    rowKey="id"
                    size="small"
                    dataSource={filteredRecords}
                    locale={{ emptyText: <Empty description="暂无中奖记录" /> }}
                    pagination={{ pageSize: 10, showSizeChanger: true }}
                    columns={[
                      { title: '中奖人', dataIndex: 'participant_name' },
                      { title: '手机号', dataIndex: 'participant_phone' },
                      { title: '奖项', dataIndex: 'prize_name' },
                      {
                        title: '中奖时间',
                        dataIndex: 'drawn_at',
                        render: (v: string) =>
                          dayjs(v).format('YYYY-MM-DD HH:mm:ss'),
                      },
                      {
                        title: '领取状态',
                        dataIndex: 'claim_status',
                        width: 140,
                        render: (v: string, r) =>
                          !r.claim_required ? (
                            <Tag>免领</Tag>
                          ) : v === 'claimed' ? (
                            <Tag color="success">
                              已领取
                              {r.claimed_at
                                ? ` · ${dayjs(r.claimed_at).format('HH:mm')}`
                                : ''}
                            </Tag>
                          ) : (
                            <Tag color="warning">待领取</Tag>
                          ),
                      },
                      {
                        title: '操作',
                        width: 280,
                        render: (_, record) => (
                          <Space>
                            {record.claim_required &&
                              record.claim_status === 'pending' && (
                                <>
                                  <Button
                                    size="small"
                                    type="link"
                                    onClick={() => void showClaimQrcode(record)}
                                  >
                                    领奖二维码
                                  </Button>
                                  <Popconfirm
                                    title="确认手动核销领奖？"
                                    description="用于中奖人手机没电或二维码丢失的情况"
                                    onConfirm={() => handleManualClaim(record)}
                                  >
                                    <Button size="small" type="link">
                                      手动核销
                                    </Button>
                                  </Popconfirm>
                                </>
                              )}
                            {record.claim_required &&
                              record.claim_status === 'claimed' && (
                                <Popconfirm
                                  title="确认撤销领奖？"
                                  description="将恢复为待领取状态"
                                  onConfirm={() => handleRevokeClaim(record)}
                                >
                                  <Button size="small" danger>
                                    撤销领奖
                                  </Button>
                                </Popconfirm>
                              )}
                          </Space>
                        ),
                      },
                    ]}
                  />
                </>
              ),
            },
          ]}
        />
      </Card>

      {/* 签到二维码弹窗 */}
      <Modal
        title="签到二维码"
        open={qrOpen}
        footer={null}
        onCancel={() => setQrOpen(false)}
        width={420}
      >
        <div style={{ textAlign: 'center' }}>
          <img
            src={qrImage || eventApi.qrcodeUrl(id)}
            alt="签到二维码"
            style={{ width: 280, height: 280 }}
          />
          <Typography.Paragraph copyable={{ text: checkinUrl }} style={{ marginTop: 12 }}>
            {checkinUrl}
          </Typography.Paragraph>
          <Typography.Text type="secondary">
            参与者用手机扫码即可签到
          </Typography.Text>
        </div>
      </Modal>

      {/* 领奖二维码弹窗 */}
      <Modal
        title="领奖二维码"
        open={claimQrOpen}
        footer={null}
        onCancel={() => setClaimQrOpen(false)}
        width={420}
      >
        <div style={{ textAlign: 'center' }}>
          {claimQrRecord && (
            <Typography.Paragraph style={{ marginBottom: 12 }}>
              <Typography.Text strong>
                {claimQrRecord.participant_name}
              </Typography.Text>
              {' · '}
              {claimQrRecord.prize_name}
            </Typography.Paragraph>
          )}
          {claimQrImage ? (
            <img
              src={claimQrImage}
              alt="领奖二维码"
              style={{ width: 280, height: 280 }}
            />
          ) : (
            <Spin />
          )}
          {claimQrRecord?.claim_url && (
            <Typography.Paragraph
              copyable={{ text: claimQrRecord.claim_url }}
              style={{ marginTop: 12 }}
            >
              {claimQrRecord.claim_url}
            </Typography.Paragraph>
          )}
          <Typography.Text type="secondary">
            中奖人用手机扫码即可核销领奖
          </Typography.Text>
        </div>
      </Modal>

      {/* 导入结果弹窗 */}
      <Modal
        title="导入结果"
        open={importOpen}
        onOk={() => setImportOpen(false)}
        onCancel={() => setImportOpen(false)}
      >
        {importResult && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Typography.Text>
              共解析 {importResult.total} 行，成功导入{' '}
              <Typography.Text strong type="success">
                {importResult.imported}
              </Typography.Text>{' '}
              条，重复跳过 {importResult.duplicated} 条，格式错误{' '}
              {importResult.invalid} 条。
            </Typography.Text>
            {importResult.errors.length > 0 && (
              <div
                style={{
                  maxHeight: 240,
                  overflow: 'auto',
                  background: '#fafafa',
                  padding: 12,
                  borderRadius: 8,
                }}
              >
                {importResult.errors.map((e, i) => (
                  <div key={i}>
                    <Typography.Text type="secondary">{e}</Typography.Text>
                  </div>
                ))}
              </div>
            )}
          </Space>
        )}
      </Modal>

      {/* 奖项编辑弹窗 */}
      <Modal
        title={editingPrize ? '编辑奖项' : '新增奖项'}
        open={prizeModalOpen}
        onOk={handleSavePrize}
        onCancel={() => setPrizeModalOpen(false)}
        destroyOnClose
      >
        <Form form={prizeForm} layout="vertical" preserve={false}>
          <Form.Item
            name="name"
            label="奖项名称"
            rules={[{ required: true, message: '请输入奖项名称' }]}
          >
            <Input placeholder="例如：一等奖" maxLength={100} />
          </Form.Item>
          <Form.Item
            name="quantity"
            label="奖项数量"
            rules={[{ required: true, message: '请输入数量' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="sort_order" label="排序权重（越小越靠前）">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="奖品描述">
            <Input placeholder="例如：iPhone 16 Pro" maxLength={255} />
          </Form.Item>
          <Form.Item
            name="draw_mode"
            label="抽奖玩法"
            extra="决定抽奖大屏使用哪种动画呈现"
          >
            <Select
              options={[
                { value: 'roll', label: '滚动名单（默认）' },
                { value: 'wheel', label: '轮盘转盘' },
                { value: 'egg', label: '砸金蛋' },
                { value: 'grid', label: '九宫格抽奖' },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="claim_required"
            label="需要现场扫码领奖"
            valuePropName="checked"
            extra="关闭后中奖即视为已领取，不生成领奖二维码"
          >
            <Switch checkedChildren="需要" unCheckedChildren="不需要" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加参与者弹窗 */}
      <Modal
        title="添加参与者"
        open={addOpen}
        onOk={handleAddParticipant}
        onCancel={() => setAddOpen(false)}
        confirmLoading={addSubmitting}
        destroyOnClose
        okText="保存"
        cancelText="取消"
      >
        <Form form={addForm} layout="vertical" preserve={false}>
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="例如：张三" maxLength={50} />
          </Form.Item>
          <Form.Item
            name="phone"
            label="手机号"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的 11 位手机号' },
            ]}
          >
            <Input placeholder="例如：13800000001" maxLength={11} />
          </Form.Item>
          <Form.Item name="department" label="部门">
            <Input placeholder="例如：技术部（可选）" maxLength={100} />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}
