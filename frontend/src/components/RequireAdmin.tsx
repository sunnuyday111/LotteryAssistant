/** 路由守卫：没有管理口令时不渲染后台，改为展示解锁页。
 *
 *  只包住主办方侧页面（后台与抽奖大屏）。签到页与领奖页是参与者侧，
 *  后端对其放行，前端也不包——所以这里无需再判断路径。
 */

import type { ReactNode } from 'react'
import { useSyncExternalStore } from 'react'
import UnlockPage from '@/pages/admin/UnlockPage'
import { getAdminToken, subscribeAdminToken } from '@/api/adminAuth'

export default function RequireAdmin({ children }: { children: ReactNode }) {
  const token = useSyncExternalStore(
    subscribeAdminToken,
    getAdminToken,
    getAdminToken,
  )

  if (!token) {
    return <UnlockPage />
  }
  return <>{children}</>
}
