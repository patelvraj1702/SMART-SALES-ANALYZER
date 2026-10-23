import { useState } from 'react'
import { useDataset } from '../context/DatasetContext'
import { PageHeader, EmptyState, DatasetBanner } from '../components/ui'
import { FileDown, Download, Package, Calendar, BarChart2 } from 'lucide-react'

function DownloadButton({ uploadId, type, label }) {
  const [loading, setLoading] = useState(false)
  const [err, setErr]         = useState('')

  const handleDownload = async () => {
    const token = localStorage.getItem('ssa_token')
    const url   = `/api/exports/${uploadId}/${type}.csv`
    setLoading(true); setErr('')
    try {
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const blob = await res.blob()
      const a    = document.createElement('a')
      a.href     = URL.createObjectURL(blob)
      a.download = label
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(a.href)
    } catch (e) {
      setErr('Export failed: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button
        onClick={handleDownload}
        disabled={loading}
        className="btn-primary text-xs px-3 py-1.5 disabled:opacity-60"
      >
        <Download className="h-3.5 w-3.5" />
        {loading ? 'Downloading…' : 'Download CSV'}
      </button>
      {err && <p className="text-xs text-red-500 mt-1">{err}</p>}
    </div>
  )
}

export default function Reports() {
  const { selectedUploadId, selectedUpload } = useDataset()

  const EXPORTS = [
    {
      icon: Package,
      title: 'Product Rankings',
      description: 'All products ranked by revenue and units sold.',
      type: 'products',
      label: 'product_rankings.csv',
      color: 'blue',
    },
    {
      icon: Calendar,
      title: 'Monthly Analytics',
      description: 'Revenue and units sold grouped by calendar month.',
      type: 'monthly',
      label: 'monthly_analytics.csv',
      color: 'green',
    },
    {
      icon: BarChart2,
      title: 'Day-of-Month Analytics',
      description: 'Revenue and units for each day of month (1–31).',
      type: 'day-of-month',
      label: 'day_of_month_analytics.csv',
      color: 'purple',
    },
  ]

  const colorMap = {
    blue:   'text-blue-600 bg-blue-50',
    green:  'text-green-600 bg-green-50',
    purple: 'text-purple-600 bg-purple-50',
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader title="Reports" subtitle="Export your analytics results as CSV files" />
      <DatasetBanner upload={selectedUpload} />

      {!selectedUploadId ? (
        <EmptyState
          icon={FileDown}
          title="No dataset selected"
          description="Go to Upload History and select a dataset to enable exports."
        />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            {EXPORTS.map(({ icon: Icon, title, description, type, label, color }) => (
              <div key={type} className="card p-6">
                <div className={`p-3 rounded-xl w-fit mb-4 ${colorMap[color]}`}>
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="font-semibold text-slate-800 mb-1">{title}</h3>
                <p className="text-sm text-slate-500 mb-4">{description}</p>
                <DownloadButton uploadId={selectedUploadId} type={type} label={label} />
              </div>
            ))}
          </div>

          <div className="card p-5 bg-slate-50">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">API Export Endpoints</h3>
            <p className="text-xs text-slate-500 mb-3">
              Use with <code className="bg-white px-1 rounded border border-slate-200 font-mono">Authorization: Bearer &lt;your-token&gt;</code>
            </p>
            <div className="space-y-1.5 font-mono text-xs text-slate-600">
              {['products', 'monthly', 'day-of-month'].map(t => (
                <div key={t} className="bg-white px-3 py-2 rounded border border-slate-200">
                  GET /api/exports/{selectedUploadId}/{t}.csv
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
