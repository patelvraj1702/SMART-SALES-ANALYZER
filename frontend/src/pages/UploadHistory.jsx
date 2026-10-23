import { useState, useEffect, useCallback } from 'react'
import { uploadsApi } from '../api'
import { useDataset } from '../context/DatasetContext'
import { PageHeader, LoadingState, EmptyState, ErrorBanner } from '../components/ui'
import { History, Trash2, Check, CheckCircle, XCircle, Clock, Loader2, AlertTriangle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function StatusBadge({ status }) {
  const cfg = {
    ready:       { cls: 'badge-success', icon: CheckCircle, label: 'Ready' },
    processing:  { cls: 'badge-info',    icon: Loader2,     label: 'Processing' },
    spark_error: { cls: 'badge-error',   icon: XCircle,     label: 'Spark Error' },
    failed:      { cls: 'badge-error',   icon: XCircle,     label: 'Failed' },
  }
  const c = cfg[status] || { cls: 'badge-warning', icon: Clock, label: status }
  const Icon = c.icon
  return (
    <span className={`${c.cls} flex items-center gap-1`}>
      <Icon className="h-3 w-3" />
      {c.label}
    </span>
  )
}

export default function UploadHistory() {
  const { selectedUploadId, selectUpload } = useDataset()
  const navigate = useNavigate()
  const [uploads,    setUploads]   = useState([])
  const [loading,    setLoading]   = useState(false)
  const [error,      setError]     = useState('')
  const [deleting,   setDeleting]  = useState(null)
  const [confirmDel, setConfirmDel]= useState(null)

  const fetchUploads = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const { data } = await uploadsApi.list()
      setUploads(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load upload history.')
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchUploads() }, [fetchUploads])

  const handleSelect = (upload) => {
    if (upload.status !== 'ready') return
    selectUpload(upload)
    navigate('/dashboard')
  }

  const handleDelete = async (upload) => {
    setDeleting(upload.id); setConfirmDel(null)
    try {
      await uploadsApi.delete(upload.id)
      setUploads(prev => prev.filter(u => u.id !== upload.id))
      if (selectedUploadId === upload.id) selectUpload(null)
    } catch (e) {
      setError(e.response?.data?.detail || 'Delete failed.')
    } finally { setDeleting(null) }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader title="Upload History" subtitle="Manage your uploaded datasets">
        <button onClick={fetchUploads} className="btn-secondary">Refresh</button>
        <button onClick={() => navigate('/upload')} className="btn-primary">New Upload</button>
      </PageHeader>

      {loading && <LoadingState />}
      {!loading && error && <ErrorBanner message={error} onRetry={fetchUploads} />}
      {!loading && !error && uploads.length === 0 && (
        <EmptyState icon={History} title="No uploads yet"
          description="Upload a sales file to get started.">
          <button onClick={() => navigate('/upload')} className="btn-primary">Upload Sales File</button>
        </EmptyState>
      )}

      {!loading && uploads.length > 0 && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">File</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Uploaded</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wide">Status</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Rows</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Accepted</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {uploads.map(upload => (
                <tr key={upload.id}
                  className={`hover:bg-slate-50 transition-colors ${
                    selectedUploadId === upload.id ? 'bg-primary-50' : ''
                  }`}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {selectedUploadId === upload.id && <Check className="h-3 w-3 text-primary-600 shrink-0" />}
                      <span className="font-medium text-slate-800 truncate max-w-[200px]">{upload.filename}</span>
                    </div>
                    {upload.error_summary && (
                      <p className="text-xs text-red-500 mt-0.5 flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" /> {upload.error_summary.slice(0, 60)}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs">
                    {new Date(upload.created_at).toLocaleDateString()}<br />
                    {new Date(upload.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={upload.status} />
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600">{upload.total_rows}</td>
                  <td className="px-4 py-3 text-right text-green-700 font-medium">{upload.accepted_rows}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      {upload.status === 'ready' && (
                        <button
                          onClick={() => handleSelect(upload)}
                          className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                            selectedUploadId === upload.id
                              ? 'bg-primary-100 text-primary-700'
                              : 'border border-slate-200 text-slate-600 hover:bg-slate-50'
                          }`}
                        >
                          {selectedUploadId === upload.id ? 'Selected' : 'Select'}
                        </button>
                      )}
                      {confirmDel === upload.id ? (
                        <div className="flex items-center gap-1">
                          <button onClick={() => handleDelete(upload)}
                            className="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Confirm</button>
                          <button onClick={() => setConfirmDel(null)}
                            className="text-xs px-2 py-1 text-slate-500 hover:bg-slate-100 rounded">Cancel</button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setConfirmDel(upload.id)}
                          disabled={deleting === upload.id}
                          className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                        >
                          {deleting === upload.id
                            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            : <Trash2 className="h-3.5 w-3.5" />}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
