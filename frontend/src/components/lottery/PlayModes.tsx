/** 抽奖大屏的多种玩法动画组件。
 *
 * 所有玩法共享同一套 props：
 *  - phase: idle / rolling / result
 *  - rollingName: 滚动时展示的候选名
 *  - winners: 中奖者列表
 *  - prizeName: 当前奖项名
 *  - remaining: 剩余名额
 *  - onStart: 点击开始抽奖
 */

import { motion, AnimatePresence } from 'framer-motion'
import { Button, Typography } from 'antd'
import { QRCodeSVG } from 'qrcode.react'
import type { DrawWinner } from '@/types'

export interface PlayProps {
  phase: 'idle' | 'rolling' | 'result'
  rollingName: string
  winners: DrawWinner[]
  prizeName: string
  remaining: number
  onStart: () => void
  disabled?: boolean
}

/** 中奖者卡片（各玩法共用）。 */
function WinnerCards({ winners }: { winners: DrawWinner[] }) {
  return (
    <motion.div
      key="result"
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 20,
        justifyContent: 'center',
        maxWidth: 1200,
      }}
    >
      {winners.map((w, idx) => (
        <motion.div
          key={w.participant_id}
          className="winner-card"
          initial={{ opacity: 0, scale: 0.5, rotate: -10 }}
          animate={{ opacity: 1, scale: 1, rotate: 0 }}
          transition={{ delay: idx * 0.15, type: 'spring', stiffness: 200 }}
        >
          <div style={{ fontSize: 40, fontWeight: 900, color: '#fde68a' }}>
            {w.name}
          </div>
          {w.department && (
            <div style={{ color: '#c4b5fd', marginTop: 4 }}>{w.department}</div>
          )}
          {w.claim_url && (
            <div style={{ marginTop: 12 }}>
              <div
                style={{
                  background: '#fff',
                  padding: 8,
                  borderRadius: 8,
                  display: 'inline-block',
                }}
              >
                <QRCodeSVG value={w.claim_url} size={96} />
              </div>
              <div style={{ color: '#c4b5fd', fontSize: 12, marginTop: 4 }}>
                扫码领奖
              </div>
            </div>
          )}
        </motion.div>
      ))}
    </motion.div>
  )
}

/** 待机提示（各玩法共用）。 */
function IdleHint({ prizeName, remaining }: { prizeName: string; remaining: number }) {
  return (
    <motion.div
      key="idle"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{ textAlign: 'center' }}
    >
      <Typography.Title level={2} style={{ color: '#a78bfa' }}>
        {prizeName ? `准备抽取「${prizeName}」` : '请先配置奖项'}
      </Typography.Title>
      {prizeName && (
        <Typography.Text style={{ color: '#c4b5fd', fontSize: 18 }}>
          剩余名额 {remaining}
        </Typography.Text>
      )}
    </motion.div>
  )
}

/** 玩法一：滚动名单（原有实现）。 */
export function RollPlay(props: PlayProps) {
  const { phase, rollingName, winners, prizeName, remaining } = props
  return (
    <AnimatePresence mode="wait">
      {phase === 'rolling' && (
        <motion.div
          key="rolling"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 1.2 }}
        >
          <div className="rolling-name">{rollingName}</div>
        </motion.div>
      )}
      {phase === 'result' && <WinnerCards winners={winners} />}
      {phase === 'idle' && <IdleHint prizeName={prizeName} remaining={remaining} />}
    </AnimatePresence>
  )
}

/** 玩法二：轮盘转盘。 */
export function WheelPlay(props: PlayProps) {
  const { phase, rollingName, winners, prizeName, remaining } = props
  const segments = 12
  const colors = ['#7c3aed', '#a855f7', '#c084fc', '#e9d5ff']

  return (
    <AnimatePresence mode="wait">
      {phase === 'rolling' && (
        <motion.div
          key="wheel"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 1.2 }}
          style={{ position: 'relative', width: 360, height: 360 }}
        >
          <motion.div
            animate={{ rotate: 360 * 6 }}
            transition={{ duration: 2, ease: 'easeOut' }}
            style={{ width: '100%', height: '100%' }}
          >
            <svg viewBox="0 0 200 200" width="360" height="360">
              {Array.from({ length: segments }).map((_, i) => {
                const angle = (360 / segments) * i
                const rad = (angle * Math.PI) / 180
                const x = 100 + 95 * Math.cos(rad)
                const y = 100 + 95 * Math.sin(rad)
                return (
                  <line
                    key={i}
                    x1="100"
                    y1="100"
                    x2={x}
                    y2={y}
                    stroke={colors[i % colors.length]}
                    strokeWidth="40"
                    strokeLinecap="butt"
                  />
                )
              })}
              <circle cx="100" cy="100" r="30" fill="#1e1b4b" />
            </svg>
          </motion.div>
          <div
            style={{
              position: 'absolute',
              top: -8,
              left: '50%',
              transform: 'translateX(-50%)',
              fontSize: 32,
              color: '#fbbf24',
            }}
          >
            ▼
          </div>
          {/* 转盘中心实时显示滚动到的候选人 */}
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 150,
              textAlign: 'center',
              fontSize: 22,
              fontWeight: 800,
              color: '#fde68a',
              pointerEvents: 'none',
            }}
          >
            {rollingName}
          </div>
        </motion.div>
      )}
      {phase === 'result' && <WinnerCards winners={winners} />}
      {phase === 'idle' && <IdleHint prizeName={prizeName} remaining={remaining} />}
    </AnimatePresence>
  )
}

/** 玩法三：砸金蛋。 */
export function EggPlay(props: PlayProps) {
  const { phase, winners, prizeName, remaining, onStart, disabled } = props
  const eggs = 9

  return (
    <AnimatePresence mode="wait">
      {phase === 'rolling' && (
        <motion.div
          key="eggs"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 24,
          }}
        >
          {Array.from({ length: eggs }).map((_, i) => (
            <motion.div
              key={i}
              animate={{
                rotate: [0, -12, 12, -12, 12, 0],
                scale: [1, 1.08, 1, 1.08, 1],
              }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                delay: i * 0.08,
              }}
              style={{
                width: 100,
                height: 130,
                borderRadius: '50% 50% 45% 45%',
                background: 'linear-gradient(160deg, #fde68a, #f59e0b)',
                boxShadow: '0 8px 24px rgba(251,191,36,0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 36,
              }}
            >
              🥚
            </motion.div>
          ))}
        </motion.div>
      )}
      {phase === 'result' && <WinnerCards winners={winners} />}
      {phase === 'idle' && (
        <motion.div
          key="idle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{ textAlign: 'center' }}
        >
          <Typography.Title level={2} style={{ color: '#a78bfa' }}>
            {prizeName ? `准备砸开「${prizeName}」金蛋` : '请先配置奖项'}
          </Typography.Title>
          {prizeName && (
            <Typography.Text style={{ color: '#c4b5fd', fontSize: 18 }}>
              剩余名额 {remaining}
            </Typography.Text>
          )}
          <div style={{ marginTop: 24 }}>
            <Button
              type="primary"
              size="large"
              onClick={onStart}
              disabled={disabled}
              style={{ minWidth: 200, height: 56, fontSize: 20 }}
            >
              砸金蛋
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

/** 玩法四：九宫格抽奖。 */
export function GridPlay(props: PlayProps) {
  const { phase, rollingName, winners, prizeName, remaining } = props
  const cells = 9

  return (
    <AnimatePresence mode="wait">
      {phase === 'rolling' && (
        <motion.div
          key="grid"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{ textAlign: 'center' }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 120px)',
              gap: 12,
              justifyContent: 'center',
            }}
          >
            {Array.from({ length: cells }).map((_, i) => (
              <motion.div
                key={i}
                animate={{
                  backgroundColor: [
                    'rgba(124,58,237,0.3)',
                    'rgba(251,191,36,0.8)',
                    'rgba(124,58,237,0.3)',
                  ],
                }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  delay: i * 0.1,
                }}
                style={{
                  width: 120,
                  height: 120,
                  borderRadius: 12,
                  border: '2px solid rgba(251,191,36,0.5)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                }}
              >
                🎁
              </motion.div>
            ))}
          </div>
          <div
            style={{
              marginTop: 20,
              fontSize: 40,
              fontWeight: 900,
              color: '#fde68a',
              textShadow: '0 0 24px rgba(251,191,36,0.7)',
            }}
          >
            {rollingName}
          </div>
        </motion.div>
      )}
      {phase === 'result' && <WinnerCards winners={winners} />}
      {phase === 'idle' && <IdleHint prizeName={prizeName} remaining={remaining} />}
    </AnimatePresence>
  )
}

/** 按玩法名渲染对应组件。 */
export function PlayRenderer({
  mode,
  ...props
}: PlayProps & { mode: string }) {
  switch (mode) {
    case 'wheel':
      return <WheelPlay {...props} />
    case 'egg':
      return <EggPlay {...props} />
    case 'grid':
      return <GridPlay {...props} />
    default:
      return <RollPlay {...props} />
  }
}