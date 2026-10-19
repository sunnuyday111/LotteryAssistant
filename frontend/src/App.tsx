import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './components/AdminLayout'
import RequireAdmin from './components/RequireAdmin'
import EventListPage from './pages/events/EventListPage'
import EventDetailPage from './pages/events/EventDetailPage'
import CheckinPage from './pages/checkin/CheckinPage'
import LotteryPage from './pages/lottery/LotteryPage'
import ClaimPage from './pages/claim/ClaimPage'
import DashboardPage from './pages/dashboard/DashboardPage'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        {/* 手机签到页（无需后台布局，公开） */}
        <Route path="/checkin/:token" element={<CheckinPage />} />

        {/* 抽奖大屏（全屏，主办方侧，需管理口令） */}
        <Route
          path="/lottery/:eventId"
          element={
            <RequireAdmin>
              <LotteryPage />
            </RequireAdmin>
          }
        />

        {/* 扫码领奖（无需后台布局，公开） */}
        <Route path="/claim/:eventId/:recordId/:code" element={<ClaimPage />} />

        {/* 管理后台（需管理口令） */}
        <Route
          path="/"
          element={
            <RequireAdmin>
              <AdminLayout />
            </RequireAdmin>
          }
        >
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
