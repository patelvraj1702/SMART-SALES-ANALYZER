import { useState, useEffect, useCallback } from 'react'
import { analyticsApi } from '../api'
import { useDataset } from '../context/DatasetContext'
import { PageHeader, LoadingState, EmptyState, ErrorBanner, DatasetBanner } from '../components/ui'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts'
import { BarChart2, ArrowUpDown } from 'lucide-react'

const COLORS = [
  '#2563eb','#7c3aed','#059669','#d97706','#dc2626',
  '#0891b2','#65a30d','#c026d3','#ea580c','#0d9488',
]

export default function ProductAnalytics() {
  const { selectedUploadId, selectedUpload } = useDataset()
  const [products, setProducts] = useState([])
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')
  const [sortBy,   setSortBy]   = useState('revenue') // 'revenue' | 'quantity'
  const [filter,   setFilter]   = useState('')

  const fetch = useCallback(async () => {
    if (!selectedUploadId) return
    setLoading(true); setError('')
    try {
      const { data } = await analyticsApi.products(selectedUploadId)
      setProducts(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load product analytics.')
    } finally { setLoading(false) }
  }, [selectedUploadId])

  useEffect(() => { fetch() }, [fetch])

  const sorted = [...products]
    .filter(p => p.product_name.toLowerCase().includes(filter.toLowerCase()))
    .sort((a, b) => sortBy === 'revenue'
      ? b.total_revenue - a.total_revenue
      : b.total_quantity - a.total_quantity
    )
  const topChart = sorted.slice(0, 10)

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader title="Product Analytics" subtitle="Revenue and quantity rankings by product" />
      <DatasetBanner upload={selectedUpload} />

      {loading && <LoadingState />}
      {!loading && error && <ErrorBanner message={error} onRetry={fetch} />}
      {!loading && !error && !selectedUploadId && (
        <EmptyState icon={BarChart2} title="No dataset selected"
          description="Select a dataset from Upload History to view product analytics." />
      )}

      {!loading && !error && products.length > 0 && (
        <>
          {/* Chart */}
          <div className="card p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-700">
                Top 10 Products by {sortBy === 'revenue' ? 'Revenue' : 'Units Sold'}
              </h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSortBy('revenue')}
                  className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                    sortBy === 'revenue' ? 'bg-primary-100 text-primary-700' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                >Revenue</button>
                <button
                  onClick={() => setSortBy('quantity')}
                  className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                    sortBy === 'quantity' ? 'bg-primary-100 text-primary-700' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                >Quantity</button>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={topChart} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 110 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number"
                  tickFormatter={sortBy === 'revenue'
                    ? v => `$${v>=1000?`${(v/1000).toFixed(0)}k`:v}`
                    : v => v}
                  tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="product_name" tick={{ fontSize: 11 }} width={110} />
                <Tooltip
                  formatter={(v, name) => [
                    sortBy === 'revenue' ? `$${v.toFixed(2)}` : v,
                    sortBy === 'revenue' ? 'Revenue' : 'Units'
                  ]}
                />
                <Bar dataKey={sortBy === 'revenue' ? 'total_revenue' : 'total_quantity'} radius={[0, 4, 4, 0]}>
                  {topChart.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Table */}
          <div className="card overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center gap-3">
              <h2 className="text-sm font-semibold text-slate-700 flex-1">All Products</h2>
              <input
                type="text"
                placeholder="Filter products…"
                value={filter}
                onChange={e => setFilter(e.target.value)}
                className="input-field w-48 text-xs py-1.5"
              />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">#</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Product</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Category</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide cursor-pointer select-none" onClick={() => setSortBy('revenue')}>
                      <span className="flex items-center justify-end gap-1">Revenue <ArrowUpDown className="h-3 w-3" /></span>
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide cursor-pointer select-none" onClick={() => setSortBy('quantity')}>
                      <span className="flex items-center justify-end gap-1">Units <ArrowUpDown className="h-3 w-3" /></span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sorted.map((p, i) => (
                    <tr key={p.product_name} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 text-slate-400 text-xs">{i + 1}</td>
                      <td className="px-4 py-3 font-medium text-slate-800">{p.product_name}</td>
                      <td className="px-4 py-3 text-slate-500 text-xs">
                        {p.category ? <span className="badge-info">{p.category}</span> : <span className="text-slate-300">—</span>}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-slate-800">
                        ${p.total_revenue.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-600">{p.total_quantity.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
