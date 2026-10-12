/** 跨端打开大屏：
 *  - Web 浏览器：window.open 新标签（同源）
 *  - Tauri 桌面端：用后端地址（http://127.0.0.1:8000）构造 URL，
 *    调起系统默认浏览器，让浏览器直接访问后端跨域资源
 */

import { API_BASE_URL } from '@/api/http'
import { isTauri } from './isTauri'

/** 构造大屏 URL。 */
function buildLotteryUrl(eventId: number): string {
  // Tauri 内 window.location 是 tauri:// 协议，外部浏览器无法访问
  // 必须用 API_BASE_URL 的 origin（桌面端默认 http://127.0.0.1:8000）
  const base = API_BASE_URL || `${window.location.protocol}//${window.location.host}`
  return `${base}/#/lottery/${eventId}`
}

/** Tauri 2 通过 shell.open 调起系统默认浏览器。 */
async function openViaSystemBrowser(url: string): Promise<void> {
  const w = window as unknown as {
    __TAURI_INTERNALS__?: { invoke: (cmd: string, args: unknown) => Promise<unknown> }
  }
  if (!w.__TAURI_INTERNALS__?.invoke) {
    throw new Error('Tauri IPC 不可用')
  }
  await w.__TAURI_INTERNALS__.invoke('plugin:shell|open', { path: url })
}

/** 打开大屏：Web 端用 window.open，Tauri 端用系统浏览器。 */
export async function openLotteryScreen(eventId: number): Promise<void> {
  const url = buildLotteryUrl(eventId)
  if (isTauri()) {
    try {
      await openViaSystemBrowser(url)
    } catch (err) {
      console.error('调起系统浏览器失败：', err)
    }
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}
