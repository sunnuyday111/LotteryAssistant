/** 管理口令的存取与订阅。
 *
 *  口令存在 localStorage：主办方解锁一次后，整个浏览器会话（含用系统浏览器
 *  打开的抽奖大屏）都能复用，无需反复输入。
 *
 *  这里刻意用「模块级状态 + 订阅」而不是 Context：axios 拦截器在 React 树之外，
 *  也需要在收到 401 时能主动清掉口令并通知界面回到解锁页。
 */

const STORAGE_KEY = 'lottery.adminToken'

/** 读取失败（隐私模式等）时降级为内存态，至少当前页面仍可用。 */
function readStorage(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

let cached: string | null = readStorage()
const listeners = new Set<() => void>()

function emit(): void {
  listeners.forEach((listener) => listener())
}

/** useSyncExternalStore 的快照，必须返回稳定值。 */
export function getAdminToken(): string | null {
  return cached
}

export function subscribeAdminToken(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

/** 保存口令并通知订阅者。 */
export function setAdminToken(token: string): void {
  const trimmed = token.trim()
  if (!trimmed) return
  cached = trimmed
  try {
    window.localStorage.setItem(STORAGE_KEY, trimmed)
  } catch {
    /* 忽略：内存态仍然有效 */
  }
  emit()
}

/** 清空口令（手动退出，或收到 401 时自动触发）。 */
export function clearAdminToken(): void {
  cached = null
  try {
    window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* 忽略 */
  }
  emit()
}
