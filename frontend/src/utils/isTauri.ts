/** 检测是否运行在 Tauri 桌面端。 */

export function isTauri(): boolean {
  if (typeof window === 'undefined') return false
  return (
    '__TAURI_INTERNALS__' in window ||
    '__TAURI__' in window ||
    window.location.protocol === 'tauri:' ||
    window.location.hostname === 'tauri.localhost'
  )
}
