import { useState, useEffect, useCallback } from 'react'
import { analyticsApi } from '../api'
import { useDataset } from '../context/DatasetContext'
import { useNavigate } from 'react-router-dom'
import {
  PageHeader, LoadingState, EmptyState, ErrorBanner, StatCard, DatasetBanner
} from '../components/ui'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  DollarSign, Package, ShoppingCart, BarChart2, Star, Upload
} from 'lucide-react'

function fmt(v) { return v >= 1000 ? `$${(v/1000).toFixed(1)}k` : `$${v.toFixed(2)}` }

export default function Dashboard() {
  const { selectedUploadId, selectedUpload } = useDataset()
  const navigate = useNavigate()

  const [summary,  setSummary]  = useState(null)
  const [products, setProducts] = useState([])
  const [monthly,  setMonthly]  = useState([])
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  const fetchAll = useCallback(async () => {
    if (!selectedUploadId) return
    setLoading(true); setError('')
    try {
      const [s, p, m] = await Promise.all([
        analyticsApi.summary(selectedUploadId),
        analyticsApi.products(selectedUploadId),
        analyticsApi.monthly(selectedUploadId),
      ])
      setSummary(s.data)
      setProducts(p.data.slice(0, 8))
      setMonthly(m.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load analytics.')
    } finally {
      setLoading(false)
    }
  }, [selectedUploadId])

  useEffect(() => { fetchAll() }, [fetchAll])

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="Dashboard" subtitle="Overview of your sales performance">
        <button onClick={() => navigate('/upload')} className="btn-primary">
          <Upload className="h-4 w-4" /> Upload Data
        </button>
      </PageHeader>

      <DatasetBanner upload={selectedUpload} />

      {loading && <LoadingState message="Loading analytics… Spark may take a moment." />}
      {!loading && error && <ErrorBanner message={error} onRetry={fetchAll} />}

      {!loading && !error && !selectedUploadId && (
        <EmptyState
          icon={BarChart2}
          title="No dataset selected"
          description="Upload a sales file to get started, then select it from Upload History."
        >
          <button onClick={() => navigate('/upload')} className="btn-primary">
            <Upload className="h-4 w-4" /> Upload Sales File
          </button>
        </EmptyState>
      )}

      {!loading && !error && summary && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard label="Total Revenue"    value={`$${summary.total_revenue.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`} icon={DollarSign} color="primary" />
            <StatCard label="Units Sold"       value={summary.total_units.toLocaleString()} icon={Package} color="green" />
            <StatCard label="Products"         value={summary.product_count} icon={BarChart2} color="purple" />
            <StatCard label="Orders"           value={summary.order_count > 0 ? summary.order_count.toLocaleString() : '—'} sub={summary.order_count === 0 ? 'No order IDs' : undefined} icon={ShoppingCart} color="amber" />
          </div>

          {/* Best product & month */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="card p-4 flex items-center gap-3">
              <div className="p-2 bg-amber-50 rounded-lg"><Star className="h-5 w-5 text-amber-500" /></div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Best Product</p>
                <p className="font-semibold text-slate-900 mt-0.5">{summary.best_product || '—'}</p>
              </div>
            </div>
            <div className="card p-4 flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg"><DollarSign className="h-5 w-5 text-green-500" /></div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Peak Month</p>
                <p className="font-semibold text-slate-900 mt-0.5">{summary.best_month || '—'}</p>
              </div>
            </div>
          </div>

          {/* Monthly revenue chart */}
          {monthly.length > 0 && (
            <div className="card p-5 mb-6">
              <h2 className="text-sm font-semibold text-slate-700 mb-4">Monthly Revenue</h2>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={monthly} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tickFormatter={v => `$${v>=1000?`${(v/1000).toFixed(0)}k`:v}`} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={v => [`$${v.toFixed(2)}`, 'Revenue']} />
                  <Line type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top products by revenue */}
          {products.length > 0 && (
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-slate-700 mb-4">Top Products by Revenue</h2>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={products} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                  <XAxis type="number" tickFormatter={v => `$${v>=1000?`${(v/1000).toFixed(0)}k`:v}`} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="product_name" tick={{ fontSize: 11 }} width={100} />
                  <Tooltip formatter={v => [`$${v.toFixed(2)}`, 'Revenue']} />
                  <Bar dataKey="total_revenue" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  )
}
