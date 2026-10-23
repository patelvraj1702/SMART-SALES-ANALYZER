export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      {children && <div className="flex items-center gap-3">{children}</div>}
    </div>
  )
}

export function Spinner({ size = 'md' }) {
  const cls = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-10 w-10' : 'h-6 w-6'
  return (
    <div className={`animate-spin rounded-full border-b-2 border-primary-600 ${cls}`} />
  )
}

export function LoadingState({ message = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <Spinner size="lg" />
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, description, children }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center gap-4">
      {Icon && <div className="p-4 bg-slate-100 rounded-full"><Icon className="h-8 w-8 text-slate-400" /></div>}
      <div>
        <p className="font-medium text-slate-700">{title}</p>
        {description && <p className="text-sm text-slate-500 mt-1">{description}</p>}
      </div>
      {children}
    </div>
  )
}

export function ErrorBanner({ message, onRetry }) {
  return (
    <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
      <div className="text-red-500 mt-0.5">⚠</div>
      <div className="flex-1">
        <p className="text-sm text-red-700">{message}</p>
        {onRetry && (
          <button onClick={onRetry} className="mt-1 text-xs text-red-600 underline">Retry</button>
        )}
      </div>
    </div>
  )
}

export function StatCard({ label, value, sub, icon: Icon, color = 'primary' }) {
  const colors = {
    primary: 'bg-primary-50 text-primary-600',
    green:   'bg-green-50 text-green-600',
    amber:   'bg-amber-50 text-amber-600',
    purple:  'bg-purple-50 text-purple-600',
    rose:    'bg-rose-50 text-rose-600',
  }
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide truncate">{label}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1 truncate">{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
        </div>
        {Icon && (
          <div className={`p-2.5 rounded-lg shrink-0 ml-3 ${colors[color]}`}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  )
}

export function DatasetBanner({ upload }) {
  if (!upload) return (
    <div className="mb-6 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
      No dataset selected. Go to <a href="/history" className="font-medium underline">Upload History</a> to select one.
    </div>
  )
  return (
    <div className="mb-6 px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800 flex items-center gap-2">
      <span className="font-medium">Dataset:</span>
      <span>{upload.filename}</span>
      <span className="text-blue-500 ml-auto text-xs">{upload.accepted_rows} valid rows</span>
    </div>
  )
}
