import { useCallback, useEffect, useRef, useState } from 'react'
import { Button, Select, Space, Statistic, Tag, Typography, message } from 'antd'
import { useParams } from 'react-router-dom'
import { drawApi, eventApi, participantApi, prizeApi, statsApi } from '@/api'
import { buildWsUrl, extractError } from '@/api/http'
import { PlayRenderer } from '@/components/lottery/PlayModes'
import type { DrawWinner, EventDetail, EventStats, Prize, WsMessage } from '@/types'

type Phase = 'idle' | 'rolling' | 'result'

export default function LotteryPage() {
  const { eventId: routeEventId } = useParams<{ eventId: string }>()
  const id = Number(routeEventId)

  const [event, setEvent] = useState<EventDetail | null>(null)
  const [prizes, setPrizes] = useState<Prize[]>([])
  const [stats, setStats] = useState<EventStats | null>(null)
  const [selectedPrize, setSelectedPrize] = useState<number | null>(null)
  const [drawCount, setDrawCount] = useState(1)

  const [phase, setPhase] = useState<Phase>('idle')
  const [rollingName, setRollingName] = useState('')
  const [winners, setWinners] = useState<DrawWinner[]>([])
  const [connected, setConnected] = useState(false)
  const [candidateNames, setCandidateNames] = useState<string[]>([])

  const wsRef = useRef<WebSocket | null>(null)
  const rollTimerRef = useRef<number | null>(null)
  const candidateNamesRef = useRef<string[]>([])

  const loadBase = useCallback(async () => {
    if (!id) return
    try {
      const [detail, prizeList, stat, parts] = await Promise.all([
        eventApi.get(id),
        prizeApi.list(id),
        statsApi.get(id),
        participantApi.list(id),
      ])
      setEvent(detail)
      setPrizes(prizeList)
      setStats(stat)
      // 滚动动画展示真实候选人姓名（仅已签到者参与抽奖）
      setCandidateNames(parts.filter((p) => p.checked_in).map((p) => p.name))
      if (prizeList.length > 0 && selectedPrize === null) {
        setSelectedPrize(prizeList[0].id)
      }
    } catch (err) {
      message.error(extractError(err))
    }
  }, [id, selectedPrize])

  const refreshStats = useCallback(async () => {
    if (!id) return
    try {
      setStats(await statsApi.get(id))
    } catch {
      /* 忽略 */
    }
  }, [id])

  // 加载基础数据
  useEffect(() => {
    void loadBase()
  }, [loadBase])

  // 建立 WebSocket 连接
  useEffect(() => {
    if (!id) return
    const ws = new WebSocket(buildWsUrl(id))
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data) as WsMessage
        if (msg.type === 'checkin') {
          void refreshStats()
        } else if (msg.type === 'draw') {
          void refreshStats()
        } else if (msg.type === 'draw_reset') {
          void refreshStats()
        }
      } catch {
        /* 忽略解析错误 */
      }
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [id, refreshStats])

  // 清理滚动定时器
  useEffect(() => {
    return () => {
      if (rollTimerRef.current !== null) {
        window.clearInterval(rollTimerRef.current)
      }
    }
  }, [])

  const startRolling = (names: string[]) => {
    candidateNamesRef.current = names
    setPhase('rolling')
    if (rollTimerRef.current !== null) {
      window.clearInterval(rollTimerRef.current)
    }
    rollTimerRef.current = window.setInterval(() => {
      const pool = candidateNamesRef.current
      if (pool.length === 0) return
      setRollingName(pool[Math.floor(Math.random() * pool.length)])
    }, 60)
  }

  const stopRolling = () => {
    if (rollTimerRef.current !== null) {
      window.clearInterval(rollTimerRef.current)
      rollTimerRef.current = null
    }
  }

  const handleDraw = async () => {
    if (!selectedPrize) {
      message.warning('请先选择奖项')
      return
    }
    const prize = prizes.find((p) => p.id === selectedPrize)
    if (!prize) return

    // 先播放滚动动画（用真实候选人姓名，名单为空时退回占位文案）
    const pool =
      candidateNames.length > 0
        ? candidateNames
        : Array.from({ length: 30 }, (_, i) => `候选 ${i + 1}`)
    startRolling(pool)

    try {
      const result = await drawApi.draw(id, {
        prize_id: selectedPrize,
        count: drawCount,
      })

      // 动画至少播放 2 秒，保证视觉效果
      await new Promise((resolve) => setTimeout(resolve, 2000))
      stopRolling()

      if (!result.success) {
        setPhase('idle')
        message.warning(result.message)
        return
      }

      setWinners(result.winners)
      setPhase('result')
      void refreshStats()
    } catch (err) {
      stopRolling()
      setPhase('idle')
      message.error(extractError(err))
    }
  }

  const handleReset = async () => {
    try {
      await drawApi.reset(id, selectedPrize ?? undefined)
      setWinners([])
      setPhase('idle')
      message.success('已重置抽奖记录')
      void refreshStats()
    } catch (err) {
      message.error(extractError(err))
    }
  }

  const currentPrize = prizes.find((p) => p.id === selectedPrize)

  return (
    <div className="lottery-screen" style={{ padding: 32 }}>
      {/* 顶部信息栏 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <Space size={32}>
          <Statistic
            title={<span style={{ color: '#c4b5fd' }}>总人数</span>}
            value={stats?.total_participants ?? 0}
            valueStyle={{ color: '#fff' }}
          />
          <Statistic
            title={<span style={{ color: '#c4b5fd' }}>已签到</span>}
            value={stats?.checked_in ?? 0}
            valueStyle={{ color: '#4ade80' }}
          />
          <Statistic
            title={<span style={{ color: '#c4b5fd' }}>签到率</span>}
            value={((stats?.checkin_rate ?? 0) * 100).toFixed(1)}
            suffix="%"
            valueStyle={{ color: '#fbbf24' }}
          />
        </Space>
        <Tag color={connected ? 'success' : 'error'}>
          {connected ? '实时连接正常' : '连接已断开'}
        </Tag>
      </div>

      <Typography.Title
        level={1}
        className="lottery-title"
        style={{ marginBottom: 8 }}
      >
        {event?.name ?? '抽奖大屏'}
      </Typography.Title>

      {/* 主展示区：按奖项配置的玩法渲染 */}
      <div
        style={{
          minHeight: 320,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '32px 0',
        }}
      >
        <PlayRenderer
          mode={currentPrize?.draw_mode ?? 'roll'}
          phase={phase}
          rollingName={rollingName}
          winners={winners}
          prizeName={currentPrize?.name ?? ''}
          remaining={
            currentPrize ? currentPrize.quantity - currentPrize.drawn_count : 0
          }
          onStart={handleDraw}
          disabled={phase === 'rolling' || !selectedPrize}
        />
      </div>

      {/* 控制区 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 16,
          flexWrap: 'wrap',
        }}
      >
        <Select
          style={{ width: 220 }}
          placeholder="选择奖项"
          value={selectedPrize ?? undefined}
          onChange={(v) => {
            setSelectedPrize(v)
            setPhase('idle')
            setWinners([])
          }}
          options={prizes.map((p) => ({
            value: p.id,
            label: `${p.name}（剩余 ${p.quantity - p.drawn_count}）`,
          }))}
        />
        <Select
          style={{ width: 140 }}
          value={drawCount}
          onChange={setDrawCount}
          options={[1, 2, 3, 5, 10].map((n) => ({
            value: n,
            label: `抽取 ${n} 人`,
          }))}
        />
        <Button
          type="primary"
          size="large"
          onClick={handleDraw}
          disabled={phase === 'rolling' || !selectedPrize}
          style={{ minWidth: 160, height: 48, fontSize: 18 }}
        >
          {phase === 'rolling' ? '抽奖中...' : '开始抽奖'}
        </Button>
        <Button size="large" onClick={handleReset} style={{ height: 48 }}>
          重置记录
        </Button>
      </div>
    </div>
  )
}
