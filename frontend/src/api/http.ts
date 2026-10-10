/** Axios 实例配置。 */

import axios from 'axios'

/** 后端 API 基础地址，可通过 VITE_API_BASE_URL 覆盖。 */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? ''

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

/** 统一错误提示提取。 */
export function extractError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((d) => d.msg ?? JSON.stringify(d)).join('；')
    }
    return error.message
  }
  if (error instanceof Error) return error.message
  return '未知错误'
}

/** 构造 WebSocket 地址。 */
export function buildWsUrl(eventId: number): string {
  if (API_BASE_URL) {
    const url = new URL(API_BASE_URL, window.location.origin)
    const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${url.host}/ws/events/${eventId}`
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/events/${eventId}`
}
