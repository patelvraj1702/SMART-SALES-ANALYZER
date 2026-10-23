import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, Upload, BarChart2, Clock,
  History, FileDown, LogOut, TrendingUp, ChevronRight
} from 'lucide-react'

const navItems = [
  { to: '/dashboard',      label: 'Dashboard',      icon: LayoutDashboard },
  { to: '/upload',         label: 'Upload Sales',   icon: Upload },
  { to: '/products',       label: 'Products',       icon: BarChart2 },
  { to: '/time-analytics', label: 'Time Analytics', icon: Clock },
  { to: '/history',        label: 'History',        icon: History },
  { to: '/reports',        label: 'Reports',        icon: FileDown },
]

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary-600 rounded-lg">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <span className="text-base font-semibold text-slate-900 leading-tight">
              Smart Sales<br />
              <span className="text-primary-600 text-xs font-medium tracking-wide uppercase">Analyzer</span>
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div className="p-3 border-t border-slate-200">
          <div className="flex items-center gap-3 px-3 py-2 mb-1">
            <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 text-sm font-semibold">
              {user?.name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium text-slate-600
                       hover:bg-red-50 hover:text-red-700 rounded-lg transition-colors duration-150"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
