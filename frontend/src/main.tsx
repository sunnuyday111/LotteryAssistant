import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App'
import './styles/global.css'

dayjs.locale('zh-cn')

// 把形如 /checkin/<token>、/claim/<eventId>/<recordId>/<code> 的 URL
// 转换为 HashRouter 所需的 #/... 形式。
// 后端 SPA fallback 会把任意路径都返回 index.html，需要在前端把 path 转 hash。
;(function rewritePathToHash() {
  const { pathname, hash, search } = window.location
  if (hash) return // 已经有 hash 不动

  // 需要转换的应用路由前缀（必须完整保留后续所有路径段，
  // 例如 /claim/1/2/c6af43c6 不能截断成 /claim/1）
  const ROUTE_PREFIXES = ['/checkin', '/lottery', '/claim', '/events']
  const isAppRoute = ROUTE_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  )
  if (!isAppRoute) return

  window.location.replace(`${pathname}#${pathname}${search ?? ''}`)
})()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ConfigProvider
    locale={zhCN}
    theme={{
      token: {
        colorPrimary: '#6d28d9',
        borderRadius: 8,
      },
    }}
  >
    <App />
  </ConfigProvider>,
)
