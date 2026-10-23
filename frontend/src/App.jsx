import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { DatasetProvider } from './context/DatasetContext'

import Login       from './pages/Login'
import Signup      from './pages/Signup'
import DashboardLayout from './layouts/DashboardLayout'
import Dashboard   from './pages/Dashboard'
import UploadSales from './pages/UploadSales'
import ProductAnalytics from './pages/ProductAnalytics'
import TimeAnalytics    from './pages/TimeAnalytics'
import UploadHistory    from './pages/UploadHistory'
import Reports          from './pages/Reports'

function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

function GuestOnly({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? <Navigate to="/dashboard" replace /> : children
}

export default function App() {
  return (
    <AuthProvider>
      <DatasetProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login"  element={<GuestOnly><Login /></GuestOnly>} />
            <Route path="/signup" element={<GuestOnly><Signup /></GuestOnly>} />
            <Route path="/" element={<RequireAuth><DashboardLayout /></RequireAuth>}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard"          element={<Dashboard />} />
              <Route path="upload"             element={<UploadSales />} />
              <Route path="products"           element={<ProductAnalytics />} />
              <Route path="time-analytics"     element={<TimeAnalytics />} />
              <Route path="history"            element={<UploadHistory />} />
              <Route path="reports"            element={<Reports />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </DatasetProvider>
    </AuthProvider>
  )
}
