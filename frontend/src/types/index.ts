/** 全局类型定义。 */

export type EventStatus = 'draft' | 'ongoing' | 'finished'

export interface EventItem {
  id: number
  name: string
  description: string | null
  location: string | null
  start_time: string | null
  end_time: string | null
  status: EventStatus
  checkin_token: string
  created_at: string
  updated_at: string
}

export interface EventDetail extends EventItem {
  participant_count: number
  checkin_count: number
  prize_count: number
}

export interface EventCreatePayload {
  name: string
  description?: string | null
  location?: string | null
  start_time?: string | null
  end_time?: string | null
}

export interface Participant {
  id: number
  event_id: number
  name: string
  phone: string
  department: string | null
  remark: string | null
  created_at: string
  checked_in: boolean
}

export interface ParticipantImportResult {
  total: number
  imported: number
  duplicated: number
  invalid: number
  errors: string[]
}

export interface CheckinResult {
  success: boolean
  message: string
  participant_name: string | null
  checked_in_at: string | null
  already_checked_in: boolean
}

/** 抽奖玩法。 */
export type DrawMode = 'roll' | 'wheel' | 'egg' | 'grid'

/** 领奖状态。 */
export type ClaimStatus = 'pending' | 'claimed'

export interface Prize {
  id: number
  event_id: number
  name: string
  quantity: number
  sort_order: number
  description: string | null
  claim_required: boolean
  draw_mode: DrawMode
  created_at: string
  drawn_count: number
}

export interface PrizePayload {
  name: string
  quantity: number
  sort_order?: number
  description?: string | null
  claim_required?: boolean
  draw_mode?: DrawMode
}

export interface DrawWinner {
  participant_id: number
  name: string
  phone: string
  department: string | null
  record_id: number | null
  claim_url: string | null
}

export interface DrawResult {
  success: boolean
  message: string
  prize_id: number
  prize_name: string
  draw_mode: DrawMode
  claim_required: boolean
  winners: DrawWinner[]
}

export interface DrawRecord {
  id: number
  event_id: number
  prize_id: number
  participant_id: number
  drawn_at: string
  claim_status: ClaimStatus
  claimed_at: string | null
  prize_name: string | null
  participant_name: string | null
  participant_phone: string | null
  claim_required: boolean
  claim_url: string | null
}

export interface ClaimInfo {
  record_id: number
  participant_name: string
  prize_name: string
  drawn_at: string
  claim_status: ClaimStatus
  claimed_at: string | null
}

export interface ClaimResult {
  success: boolean
  message: string
  info: ClaimInfo | null
  already_claimed: boolean
}

export interface ClaimStats {
  pending: number
  claimed: number
  /** 奖项配置为无需现场领奖的记录数。 */
  exempt: number
  total: number
}

export interface PrizeStat {
  prize_id: number
  prize_name: string
  quantity: number
  drawn_count: number
  claim_required: boolean
  pending_count: number
  claimed_count: number
}

export interface EventStats {
  event_id: number
  event_name: string
  total_participants: number
  checked_in: number
  not_checked_in: number
  checkin_rate: number
  prize_stats: PrizeStat[]
  claim_pending: number
  claim_claimed: number
  claim_exempt: number
}

export interface CheckinEventInfo {
  event_id: number
  name: string
  location: string | null
  start_time: string | null
  status: EventStatus
}

/** WebSocket 推送消息。 */
export type WsMessage =
  | { type: 'connected'; event_id: number }
  | {
      type: 'checkin'
      event_id: number
      participant_name: string | null
      checked_in_count: number
    }
  | {
      type: 'draw'
      event_id: number
      prize_id: number
      prize_name: string
      winners: DrawWinner[]
    }
  | { type: 'draw_reset'; event_id: number; prize_id: number | null }
  | { type: 'claim'; event_id: number; record_id: number; stats: ClaimStats }
