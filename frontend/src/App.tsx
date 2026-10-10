import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './components/AdminLayout'
import EventListPage from './pages/events/EventListPage'
import EventDetailPage from './pages/events/EventDetailPage'
import CheckinPage from './pages/checkin/CheckinPage'
import LotteryPage from './pages/lottery/LotteryPage'
import DashboardPage from './pages/dashboard/DashboardPage'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        {/* 手机签到页（无需后台布局） */}
        <Route path="/checkin/:token" element={<CheckinPage />} />

        {/* 抽奖大屏（全屏） */}
        <Route path="/lottery/:eventId" element={<LotteryPage />} />

        {/* 管理后台 */}
        <Route path="/" element={<AdminLayout />}>
          <Route index element={<Navigate to="/events" replace />} />
          <Route path="events" element={<EventListPage />} />
          <Route path="events/:eventId" element={<EventDetailPage />} />
          <Route path="events/:eventId/dashboard" element={<DashboardPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/events" replace />} />
      </Routes>
    </HashRouter>
  )
}
