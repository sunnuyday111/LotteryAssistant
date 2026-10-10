/** 跨端打开大屏：
 *  - Web 浏览器：window.open 新标签
 *  - Tauri 桌面端：调用自定义 Rust 命令新建一个原生 WebviewWindow
 */

import { isTauri } from './isTauri'

/** Tauri 2 通过自定义命令新建大屏窗口（Rust 端已注册 open_lottery_window）。 */
async function openTauriWindow(eventId: number): Promise<void> {
  const w = window as unknown as {
    __TAURI_INTERNALS__?: { invoke: (cmd: string, args: unknown) => Promise<unknown> }
  }
  if (!w.__TAURI_INTERNALS__?.invoke) {
    throw new Error('Tauri IPC 不可用')
  }
  await w.__TAURI_INTERNALS__.invoke('open_lottery_window', { eventId })
}

/** 在新窗口/原生 WebviewWindow 中打开大屏。 */
export async function openLotteryScreen(eventId: number): Promise<void> {
  if (isTauri()) {
    try {
      await openTauriWindow(eventId)
    } catch (err) {
      console.error('Tauri 新建大屏窗口失败：', err)
    }
    return
  }
  const base = `${window.location.protocol}//${window.location.host}`
  const url = `${base}/#/lottery/${eventId}`
  window.open(url, '_blank', 'noopener,noreferrer')
}
