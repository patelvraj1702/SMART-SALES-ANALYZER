import { useState, useEffect, useCallback } from 'react'
import { analyticsApi } from '../api'
import { useDataset } from '../context/DatasetContext'
import { PageHeader, LoadingState, EmptyState, ErrorBanner, DatasetBanner, StatCard } from '../components/ui'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { Calendar, TrendingUp, Info } from 'lucide-react'

export default function TimeAnalytics() {
  const { selectedUploadId, selectedUpload } = useDataset()
  const [monthly,    setMonthly]    = useState([])
  const [dayOfMonth, setDayOfMonth] = useState([])
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState('')

  const fetch = useCallback(async () => {
    if (!selectedUploadId) return
    setLoading(true); setError('')
    try {
      const [m, d] = await Promise.all([
        analyticsApi.monthly(selectedUploadId),
        analyticsApi.dayOfMonth(selectedUploadId),
      ])
      setMonthly(m.data)
      setDayOfMonth(d.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load time analytics.')
    } finally { setLoading(false) }
  }, [selectedUploadId])

  useEffect(() => { fetch() }, [fetch])

  const bestMonth = monthly.length ? monthly.reduce((a, b) => a.revenue > b.revenue ? a : b) : null
  const bestDay   = dayOfMonth.length ? dayOfMonth.reduce((a, b) => a.revenue > b.revenue ? a : b) : null

  // Fill all 31 days for display (missing days = 0)
  const allDays = Array.from({ length: 31 }, (_, i) => {
    const found = dayOfMonth.find(d => d.day === i + 1)
    return found || { day: i + 1, revenue: 0, units_sold: 0 }
  })

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader title="Time Analytics" subtitle="Sales trends by month and day of month" />
      <DatasetBanner upload={selectedUpload} />

      {loading && <LoadingState />}
      {!loading && error && <ErrorBanner message={error} onRetry={fetch} />}
      {!loading && !error && !selectedUploadId && (
        <EmptyState icon={Calendar} title="No dataset selected"
          description="Select a dataset from Upload History to view time analytics." />
      )}

      {!loading && !error && selectedUploadId && monthly.length === 0 && dayOfMonth.length === 0 && (
        <div className="card p-6 flex items-start gap-3">
          <Info className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-slate-700">No date information available</p>
            <p className="text-sm text-slate-500 mt-1">
              This dataset does not have a mapped date column, or the dates could not be parsed.
              Monthly and day-of-month analytics require a valid transaction date.
            </p>
          </div>
        </div>
      )}

      {!loading && !error && (monthly.length > 0 || dayOfMonth.length > 0) && (
        <>
          {/* Highlights */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <StatCard
              label="Peak Revenue Month"
              value={bestMonth?.month || '—'}
              sub={bestMonth ? `$${bestMonth.revenue.toFixed(2)}` : undefined}
              icon={TrendingUp} color="primary"
            />
            <StatCard
              label="Peak Revenue Day of Month"
              value={bestDay ? `Day ${bestDay.day}` : '—'}
              sub={bestDay ? `$${bestDay.revenue.toFixed(2)}` : undefined}
              icon={Calendar} color="green"
            />
          </div>

          {/* Monthly */}
          {monthly.length > 0 && (
            <div className="card p-5 mb-6">
              <h2 className="text-sm font-semibold text-slate-700 mb-4">Monthly Revenue & Units Sold</h2>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={monthly} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left"  tickFormatter={v => `$${v>=1000?`${(v/1000).toFixed(0)}k`:v}`} tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(v, name) => [
                      name === 'revenue' ? `$${v.toFixed(2)}` : v,
                      name === 'revenue' ? 'Revenue' : 'Units Sold',
                    ]}
                  />
                  <Legend formatter={n => n === 'revenue' ? 'Revenue' : 'Units Sold'} />
                  <Line yAxisId="left"  type="monotone" dataKey="revenue"    stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
                  <Line yAxisId="right" type="monotone" dataKey="units_sold" stroke="#059669" strokeWidth={2} dot={{ r: 3 }} strokeDasharray="4 2" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Day of month */}
          {dayOfMonth.length > 0 && (
            <div className="card p-5 mb-6">
              <h2 className="text-sm font-semibold text-slate-700 mb-4">Revenue by Day of Month (1–31)</h2>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={allDays} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="day" tick={{ fontSize: 10 }} interval={1} />
                  <YAxis tickFormatter={v => `$${v>=1000?`${(v/1000).toFixed(0)}k`:v}`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={v => [`$${v.toFixed(2)}`, 'Revenue']} labelFormatter={l => `Day ${l}`} />
                  <Bar dataKey="revenue" fill="#2563eb" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Monthly table */}
          {monthly.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-200">
                <h2 className="text-sm font-semibold text-slate-700">Monthly Breakdown</h2>
              </div>
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Month</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Revenue</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Units Sold</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {monthly.map(m => (
                    <tr key={m.month} className={`hover:bg-slate-50 ${m.month === bestMonth?.month ? 'bg-primary-50' : ''}`}>
                      <td className="px-4 py-3 font-medium text-slate-800 flex items-center gap-2">
                        {m.month}
                        {m.month === bestMonth?.month && <span className="badge-info text-xs">Peak</span>}
                      </td>
                      <td className="px-4 py-3 text-right">${m.revenue.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right text-slate-600">{m.units_sold.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
