import { useState, useCallback } from 'react'
import { uploadsApi } from '../api'
import { PageHeader, ErrorBanner, Spinner } from '../components/ui'
import { Upload, FileText, CheckCircle, XCircle, AlertTriangle, Loader2, Calendar, Clock, AlertCircle } from 'lucide-react'

const CANONICAL_FIELDS = [
  { key: 'product_name', label: 'Product Name', required: true },
  { key: 'quantity',     label: 'Quantity',     required: true },
  { key: 'unit_price',   label: 'Unit Price',   required: false },
  { key: 'line_total',  label: 'Line Total (alt. to price)', required: false },
  { key: 'transaction_date', label: 'Date Column', required: false },
  { key: 'transaction_time', label: 'Time Column (optional)', required: false },
  { key: 'category',    label: 'Category',      required: false },
  { key: 'order_id',    label: 'Order ID',      required: false },
]

const STEP = { IDLE: 0, PREVIEWING: 1, MAPPING: 2, CONFIRMING: 3, DONE: 4 }

export default function UploadSales() {
  const [file,           setFile]           = useState(null)
  const [preview,        setPreview]        = useState(null)
  const [mapping,        setMapping]        = useState({})
  const [dateFormatPref, setDateFormatPref] = useState('auto')
  const [step,           setStep]           = useState(STEP.IDLE)
  const [loading,        setLoading]        = useState(false)
  const [error,          setError]          = useState('')
  const [result,         setResult]         = useState(null)
  const [dragging,       setDragging]       = useState(false)

  const handleFile = useCallback(async (f) => {
    if (!f) return
    const allowed = ['.csv', '.xlsx', '.xls']
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) { setError('Only CSV and XLSX files are supported.'); return }

    setFile(f); setError(''); setStep(STEP.PREVIEWING); setLoading(true)
    try {
      const { data } = await uploadsApi.preview(f)
      setPreview(data)
      
      // Auto-map common column names with normalization
      const autoMap = {}
      const colCleanMap = {}
      data.columns.forEach(c => {
        colCleanMap[c.toLowerCase().trim()] = c
        colCleanMap[c.toLowerCase().replace(/[\s_-]+/g, '_').trim()] = c
        colCleanMap[c.toLowerCase().replace(/[\s_-]+/g, ' ').trim()] = c
      })

      const AUTO = {
        product_name: ['product_name', 'product', 'item', 'item name', 'product name', 'description'],
        quantity: ['quantity', 'qty', 'units', 'amount', 'count'],
        unit_price: ['unit_price', 'price', 'unit price', 'rate', 'cost per unit'],
        transaction_date: [
          'transaction_date', 'transaction date', 'date', 'order_date', 'order date',
          'sales_date', 'sale_date', 'bill_date', 'invoice_date', 'created_at', 'timestamp'
        ],
        transaction_time: [
          'transaction_time', 'transaction time', 'time', 'order_time', 'order time', 'sale_time'
        ],
        category: ['category', 'cat', 'type', 'department', 'group'],
        order_id: ['order_id', 'order id', 'orderid', 'order #', 'order number'],
        line_total: ['line_total', 'total', 'line total', 'subtotal', 'extended price'],
      }

      for (const [field, aliases] of Object.entries(AUTO)) {
        for (const alias of aliases) {
          if (colCleanMap[alias]) { autoMap[field] = colCleanMap[alias]; break }
        }
      }

      // If backend detected date/time columns via cell inspection, prioritize them
      if (data.temporal_analysis) {
        const ta = data.temporal_analysis
        if (ta.detected_date_col) autoMap.transaction_date = ta.detected_date_col
        if (ta.detected_time_col) autoMap.transaction_time = ta.detected_time_col
      }

      setMapping(autoMap)
      setStep(STEP.MAPPING)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to read file.')
      setStep(STEP.IDLE)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleDrop = (e) => {
    e.preventDefault(); setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleConfirm = async () => {
    if (!mapping.product_name || !mapping.quantity) {
      setError('Product Name and Quantity must be mapped.')
      return
    }
    if (!mapping.unit_price && !mapping.line_total) {
      setError('Either Unit Price or Line Total must be mapped to calculate revenue.')
      return
    }
    setError(''); setLoading(true); setStep(STEP.CONFIRMING)
    try {
      const fullMapping = {
        ...mapping,
        date_format_pref: dateFormatPref,
      }
      const { data } = await uploadsApi.confirm(file, fullMapping)
      setResult(data)
      setStep(STEP.DONE)
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed.')
      setStep(STEP.MAPPING)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setFile(null); setPreview(null); setMapping({})
    setDateFormatPref('auto'); setStep(STEP.IDLE); setError(''); setResult(null)
  }

  const ta = preview?.temporal_analysis

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader title="Upload Sales Data" subtitle="Import CSV or XLSX files with flexible date and time detection" />

      {error && <div className="mb-4"><ErrorBanner message={error} /></div>}

      {/* Step 0: Drop zone */}
      {step === STEP.IDLE && (
        <div
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${
            dragging ? 'border-primary-400 bg-primary-50' : 'border-slate-200 hover:border-primary-300 hover:bg-slate-50'
          }`}
          onClick={() => document.getElementById('file-input').click()}
        >
          <input id="file-input" type="file" accept=".csv,.xlsx,.xls" className="hidden"
            onChange={e => handleFile(e.target.files[0])} />
          <Upload className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-700 font-medium mb-1">Drag & drop your sales file here</p>
          <p className="text-slate-400 text-sm mb-4">or click to browse</p>
          <div className="flex items-center justify-center gap-4 text-xs text-slate-400">
            <span>✓ CSV</span><span>✓ XLSX</span><span>✓ Multi-Sheet Support</span><span>✓ Intelligent Date/Time Detection</span>
          </div>
        </div>
      )}

      {/* Step 1: Previewing spinner */}
      {step === STEP.PREVIEWING && loading && (
        <div className="card p-12 flex flex-col items-center gap-4">
          <Spinner size="lg" />
          <p className="text-slate-500 text-sm">Reading file and analyzing date formats…</p>
        </div>
      )}

      {/* Step 2: Column mapping & Date/Time Inspection */}
      {step === STEP.MAPPING && preview && (
        <div className="space-y-6">
          {/* File Raw Preview */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-700">File Preview</h2>
                <p className="text-xs text-slate-500 mt-0.5">{preview.row_count} rows · {preview.columns.length} columns detected</p>
              </div>
              <FileText className="h-5 w-5 text-slate-400" />
            </div>
            <div className="overflow-x-auto">
              <table className="text-xs w-full">
                <thead>
                  <tr className="bg-slate-50">
                    {preview.columns.map(c => <th key={c} className="px-3 py-2 text-left text-slate-600 font-medium border-b border-slate-200">{c}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {preview.sample_rows.map((row, i) => (
                    <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                      {preview.columns.map(c => <td key={c} className="px-3 py-2 text-slate-600 truncate max-w-[140px]">{row[c] ?? ''}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Date & Time Intelligence Card */}
          {ta && (
            <div className="card p-5 border-l-4 border-l-primary-500">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-primary-600" />
                  <h2 className="text-sm font-semibold text-slate-800">Date & Time Intelligence</h2>
                </div>
                <div>
                  {ta.temporal_type === 'date_and_time' && (
                    <span className="badge bg-green-100 text-green-700 font-medium">✓ Date & Time Detected</span>
                  )}
                  {ta.temporal_type === 'date_only' && (
                    <span className="badge bg-blue-100 text-blue-700 font-medium">✓ Calendar Date Detected</span>
                  )}
                  {ta.temporal_type === 'time_only' && (
                    <span className="badge bg-amber-100 text-amber-700 font-medium">⚠ Time Only Detected</span>
                  )}
                  {ta.temporal_type === 'none' && (
                    <span className="badge bg-slate-100 text-slate-600">No Date/Time Column Detected</span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4 text-xs">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 block">Detected Date Field</span>
                  <span className="font-semibold text-slate-800">{ta.detected_date_col || 'None'}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 block">Detected Time Field</span>
                  <span className="font-semibold text-slate-800">{ta.detected_time_col || 'None (or combined)'}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 block">Sample Parsed Valid</span>
                  <span className="font-semibold text-slate-800">{ta.valid_dates_count} dates · {ta.valid_times_count} times</span>
                </div>
              </div>

              {/* Sample conversions */}
              {ta.sample_evaluations?.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-slate-600 mb-1.5">Sample Normalized Values:</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {ta.sample_evaluations.slice(0, 4).map((evalItem, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-100">
                        <span className="text-slate-500 truncate max-w-[120px] font-mono">{evalItem.raw}</span>
                        <div className="flex items-center gap-1.5">
                          {evalItem.normalized_date && (
                            <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded font-mono text-[11px]">{evalItem.normalized_date}</span>
                          )}
                          {evalItem.normalized_time && (
                            <span className="px-1.5 py-0.5 bg-purple-50 text-purple-700 rounded font-mono text-[11px]">{evalItem.normalized_time}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Date Format Preference for Ambiguity */}
              <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-700 block">Date Format Interpretation</label>
                  <p className="text-[11px] text-slate-400">Choose how numeric dates like "03/04/2026" should be interpreted</p>
                </div>
                <select
                  value={dateFormatPref}
                  onChange={e => setDateFormatPref(e.target.value)}
                  className="input-field text-xs py-1.5 px-3 w-full sm:w-auto"
                >
                  <option value="auto">Auto-detect ({ta.detected_ambiguity ? 'Ambiguous: defaults to Day-first' : 'Standard'})</option>
                  <option value="DMY">Day / Month / Year (e.g. 15/09/2026)</option>
                  <option value="MDY">Month / Day / Year (e.g. 09/15/2026)</option>
                  <option value="YMD">Year / Month / Day (e.g. 2026/09/15)</option>
                </select>
              </div>

              {ta.temporal_type === 'time_only' && (
                <div className="mt-3 p-3 bg-amber-50 rounded-lg flex items-start gap-2 text-xs text-amber-800">
                  <AlertCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>This file only contains time values. Time data will be preserved, but monthly and day-of-month charts require calendar dates.</span>
                </div>
              )}
            </div>
          )}

          {/* Column Mapping Section */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-1">Map Columns</h2>
            <p className="text-xs text-slate-500 mb-4">Match your file's columns to the standard fields. Fields marked * are required.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {CANONICAL_FIELDS.map(({ key, label, required }) => (
                <div key={key}>
                  <label className="label text-xs">
                    {label} {required && <span className="text-red-500">*</span>}
                  </label>
                  <select
                    value={mapping[key] || ''}
                    onChange={e => setMapping(m => ({ ...m, [key]: e.target.value || undefined }))}
                    className="input-field text-xs"
                  >
                    <option value="">— not mapped —</option>
                    {preview.columns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-3 mt-6">
              <button onClick={handleConfirm} className="btn-primary">
                <CheckCircle className="h-4 w-4" /> Import & Analyze
              </button>
              <button onClick={reset} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Processing */}
      {step === STEP.CONFIRMING && (
        <div className="card p-12 flex flex-col items-center gap-4 text-center">
          <Loader2 className="h-12 w-12 text-primary-600 animate-spin" />
          <div>
            <p className="font-medium text-slate-800">Processing with Apache Spark…</p>
            <p className="text-sm text-slate-500 mt-1">Ingesting dataset and computing sales analytics.</p>
          </div>
        </div>
      )}

      {/* Step 4: Done */}
      {step === STEP.DONE && result && (
        <div className="card p-8 text-center">
          {result.status === 'ready' ? (
            <>
              <CheckCircle className="h-14 w-14 text-green-500 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-slate-900 mb-2">Upload Complete!</h2>
              <p className="text-slate-500 text-sm mb-4">{result.filename}</p>
              <div className="flex justify-center gap-6 mb-6 text-sm">
                <div className="text-center"><p className="text-2xl font-bold text-slate-900">{result.accepted_rows}</p><p className="text-slate-500">Accepted</p></div>
                <div className="text-center"><p className="text-2xl font-bold text-red-500">{result.rejected_rows}</p><p className="text-slate-500">Rejected</p></div>
              </div>
              <div className="flex gap-3 justify-center">
                <a href="/dashboard" className="btn-primary">View Dashboard</a>
                <button onClick={reset} className="btn-secondary">Upload Another</button>
              </div>
            </>
          ) : (
            <>
              <XCircle className="h-14 w-14 text-red-500 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-slate-900 mb-2">Processing Error</h2>
              <p className="text-slate-500 text-sm mb-4">{result.error_summary}</p>
              <button onClick={reset} className="btn-secondary">Try Again</button>
            </>
          )}
        </div>
      )}

      {/* Format guide */}
      {step === STEP.IDLE && (
        <div className="mt-6 card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Supported Column Formats</h3>
          <p className="text-xs text-slate-500 mb-3">Your file can contain any combination of these fields:</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            {['Product Name *', 'Quantity *', 'Unit Price / Line Total *', 'Date (any format)', 'Time (optional)', 'Category', 'Order ID'].map(f => (
              <div key={f} className="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-lg text-slate-600">
                <span className="h-1.5 w-1.5 rounded-full bg-primary-400 shrink-0" />
                {f}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
