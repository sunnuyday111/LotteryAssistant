/** 后端 API 封装。 */

import { http } from './http'
import type {
  CheckinEventInfo,
  CheckinResult,
  DrawRecord,
  DrawResult,
  EventCreatePayload,
  EventDetail,
  EventItem,
  EventStats,
  Participant,
  ParticipantImportResult,
  Prize,
  PrizePayload,
} from '@/types'

// ---------- 活动 ----------
export const eventApi = {
  list: () => http.get<EventItem[]>('/api/events').then((r) => r.data),
  get: (id: number) =>
    http.get<EventDetail>(`/api/events/${id}`).then((r) => r.data),
  create: (data: EventCreatePayload) =>
    http.post<EventItem>('/api/events', data).then((r) => r.data),
  update: (id: number, data: Partial<EventCreatePayload> & { status?: string }) =>
    http.put<EventItem>(`/api/events/${id}`, data).then((r) => r.data),
  remove: (id: number) => http.delete(`/api/events/${id}`),
  checkinUrl: (id: number) =>
    http
      .get<{ token: string; url: string }>(`/api/events/${id}/checkin-url`)
      .then((r) => r.data),
  qrcodeUrl: (id: number) => `${http.defaults.baseURL ?? ''}/api/events/${id}/qrcode`,
}

// ---------- 参与者 ----------
export const participantApi = {
  list: (eventId: number) =>
    http
      .get<Participant[]>(`/api/events/${eventId}/participants`)
      .then((r) => r.data),
  create: (eventId: number, data: { name: string; phone: string; department?: string; remark?: string }) =>
    http
      .post<Participant>(`/api/events/${eventId}/participants`, data)
      .then((r) => r.data),
  remove: (eventId: number, participantId: number) =>
    http.delete(`/api/events/${eventId}/participants/${participantId}`),
  import: (eventId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http
      .post<ParticipantImportResult>(
        `/api/events/${eventId}/participants/import`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      )
      .then((r) => r.data)
  },
}

// ---------- 签到 ----------
export const checkinApi = {
  info: (token: string) =>
    http.get<CheckinEventInfo>(`/api/checkin/${token}`).then((r) => r.data),
  submit: (token: string, data: { phone: string; name?: string }) =>
    http.post<CheckinResult>(`/api/checkin/${token}`, data).then((r) => r.data),
  manual: (eventId: number, participantId: number) =>
    http
      .post<CheckinResult>(`/api/checkin/${eventId}/manual/${participantId}`)
      .then((r) => r.data),
  cancel: (eventId: number, participantId: number) =>
    http.delete(`/api/checkin/${eventId}/manual/${participantId}`),
}

// ---------- 奖项 ----------
export const prizeApi = {
  list: (eventId: number) =>
    http.get<Prize[]>(`/api/events/${eventId}/prizes`).then((r) => r.data),
  create: (eventId: number, data: PrizePayload) =>
    http.post<Prize>(`/api/events/${eventId}/prizes`, data).then((r) => r.data),
  update: (eventId: number, prizeId: number, data: Partial<PrizePayload>) =>
    http
      .put<Prize>(`/api/events/${eventId}/prizes/${prizeId}`, data)
      .then((r) => r.data),
  remove: (eventId: number, prizeId: number) =>
    http.delete(`/api/events/${eventId}/prizes/${prizeId}`),
}

// ---------- 抽奖 ----------
export const drawApi = {
  draw: (
    eventId: number,
    data: { prize_id: number; count: number; allow_repeat_winner?: boolean },
  ) =>
    http
      .post<DrawResult>(`/api/events/${eventId}/draws`, data)
      .then((r) => r.data),
  records: (eventId: number) =>
    http.get<DrawRecord[]>(`/api/events/${eventId}/draws`).then((r) => r.data),
  reset: (eventId: number, prizeId?: number) =>
    http.delete(`/api/events/${eventId}/draws`, {
      params: prizeId ? { prize_id: prizeId } : {},
    }),
}

// ---------- 统计 ----------
export const statsApi = {
  get: (eventId: number) =>
    http.get<EventStats>(`/api/events/${eventId}/stats`).then((r) => r.data),
}

// ---------- 导出 ----------
export const exportApi = {
  checkins: (eventId: number) =>
    http.get(`/api/events/${eventId}/export/checkins`, {
      responseType: 'blob',
    }),
  draws: (eventId: number) =>
    http.get(`/api/events/${eventId}/export/draws`, { responseType: 'blob' }),
}
