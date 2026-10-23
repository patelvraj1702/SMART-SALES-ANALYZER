import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { TrendingUp, Eye, EyeOff, Loader2 } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const navigate   = useNavigate()

  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPw,   setShowPw]   = useState(false)
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!email || !password) { setError('Please fill in all fields.'); return }
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-primary-600 rounded-2xl mb-4 shadow-lg shadow-primary-100">
            <TrendingUp className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Smart Sales Analyzer</h1>
          <p className="text-slate-500 text-sm mt-1">Sign in to your account</p>
        </div>

        <div className="card p-8">
          {error && (
            <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label htmlFor="login-email" className="label">Email address</label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="input-field"
                autoComplete="email"
                required
              />
            </div>
            <div>
              <label htmlFor="login-password" className="label">Password</label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pr-10"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-2.5"
            >
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Signing in…</> : 'Sign in'}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-500">
            Don't have an account?{' '}
            <Link to="/signup" className="text-primary-600 font-medium hover:text-primary-700">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
