/** Axios 实例配置。 */

import axios, { type AxiosRequestConfig } from 'axios'
import { isTauri } from '@/utils/isTauri'
import { clearAdminToken, getAdminToken } from './adminAuth'

/** 扩展请求配置，附加重试计数器。 */
type RetryableConfig = AxiosRequestConfig & { __retryCount?: number }

/** 与后端 security.ADMIN_TOKEN_HEADER 保持一致。 */
export const ADMIN_TOKEN_HEADER = 'X-Admin-Token'

/** 后端 API 基础地址：
 *  - 显式 VITE_API_BASE_URL 优先
 *  - 浏览器中（Vite dev / 普通部署）使用相对路径，由 Vite proxy 或同源 nginx 转发
 *  - Tauri 桌面端默认指向本机 8000 端口（需先启动后端） */
export const API_BASE_URL: string = (() => {
  const envBase = import.meta.env.VITE_API_BASE_URL
  if (envBase) return envBase
  return isTauri() ? 'http://127.0.0.1:8000' : ''
})()

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

/** 为每个请求初始化重试计数器，并按需附加管理口令。 */
http.interceptors.request.use((config) => {
  if (config && (config as { __retryCount?: number }).__retryCount === undefined) {
    ;(config as { __retryCount?: number }).__retryCount = 0
  }
  // 已解锁才带口令：未解锁时保持请求「干净」，401 才能被识别为需要解锁，
  // 而不是被误判成别的错误。
  const token = getAdminToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers[ADMIN_TOKEN_HEADER] = token
  }
  return config
})

/** 响应拦截器：把 200+空 body 当错误（防御 Tauri 协议异常），
 *  并对桌面端的网络错误做指数退避重试。 */
http.interceptors.response.use(
  (response) => {
    if (response.status >= 200 && response.status < 300) {
      return response
    }
    return Promise.reject(new Error(`HTTP ${response.status}`))
  },
  async (error) => {
    // 口令失效（被改过、服务重启后自动生成的口令变了）时清空本地口令，
    // 订阅者会据此把界面切回解锁页。
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      clearAdminToken()
      return Promise.reject(error)
    }
    if (!isTauri()) return Promise.reject(error)
    const config = error.config as RetryableConfig | undefined
    if (!config || config.__retryCount === undefined) return Promise.reject(error)
    const isGet = (config.method ?? 'get').toLowerCase() === 'get'
    const transient =
      !error.response || error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED'
    if (!isGet || !transient || config.__retryCount >= 8) return Promise.reject(error)

    config.__retryCount += 1
    const delay = Math.min(250 * 2 ** (config.__retryCount - 1), 2000)
    await new Promise((r) => setTimeout(r, delay))
    return http.request(config)
  },
)

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

/** 规范化可能为 null/undefined 的数组响应。 */
export function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : []
}

/** 构造 WebSocket 地址。
 *
 *  大屏的实时通道同样需要管理口令，而浏览器无法为 WebSocket 自定义请求头，
 *  因此按后端 security.ADMIN_TOKEN_QUERY 的约定走查询参数。 */
export function buildWsUrl(eventId: number): string {
  // 有 API_BASE_URL 时以其协议为准（Tauri 下窗口协议是 tauri:，但后端仍是 http），
  // 同源部署才退回 window.location。
  const base = API_BASE_URL ? new URL(API_BASE_URL, window.location.origin) : null
  const protocol = (base?.protocol ?? window.location.protocol) === 'https:' ? 'wss:' : 'ws:'
  const host = base?.host ?? window.location.host
  const url = `${protocol}//${host}/ws/events/${eventId}`
  const token = getAdminToken()
  return token ? `${url}?token=${encodeURIComponent(token)}` : url
}
