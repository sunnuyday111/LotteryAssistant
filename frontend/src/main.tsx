import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App'
import './styles/global.css'

dayjs.locale('zh-cn')

// 把形如 /checkin/<token> 的 URL 转换为 HashRouter 所需的 #/checkin/<token>
// 后端 SPA fallback 会把任意路径都返回 index.html，需要在前端把 path 转 hash
;(function rewritePathToHash() {
  const { pathname, hash, search } = window.location
  if (hash) return // 已经有 hash 不动
  // 仅处理签到/抽奖路径
  const m = pathname.match(/^\/(checkin|lottery|events)(?:\/([^/]+))?/)
  if (!m) return
  const seg = m[1]
  const id = m[2]
  const hashPath = id ? `/${seg}/${id}` : `/${seg}`
  window.location.replace(`${window.location.pathname}#${hashPath}${search ?? ''}`)
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
