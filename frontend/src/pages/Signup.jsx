import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { TrendingUp, Eye, EyeOff, Loader2, Check, X } from 'lucide-react'

function PasswordRule({ met, label }) {
  return (
    <span className={`flex items-center gap-1 text-xs ${met ? 'text-green-600' : 'text-slate-400'}`}>
      {met ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
      {label}
    </span>
  )
}

export default function Signup() {
  const { signup } = useAuth()
  const navigate   = useNavigate()

  const [name,    setName]    = useState('')
  const [email,   setEmail]   = useState('')
  const [pw,      setPw]      = useState('')
  const [cpw,     setCpw]     = useState('')
  const [showPw,  setShowPw]  = useState(false)
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const rules = {
    length:  pw.length >= 8,
    upper:   /[A-Z]/.test(pw),
    number:  /\d/.test(pw),
    match:   pw === cpw && cpw.length > 0,
  }
  const allRulesMet = Object.values(rules).every(Boolean)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!name || !email || !pw || !cpw) { setError('Please fill in all fields.'); return }
    if (!allRulesMet) { setError('Please meet all password requirements.'); return }
    setLoading(true)
    try {
      await signup(name, email, pw, cpw)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Sign up failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-primary-600 rounded-2xl mb-4 shadow-lg shadow-primary-100">
            <TrendingUp className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
          <p className="text-slate-500 text-sm mt-1">Start analyzing your sales data today</p>
        </div>

        <div className="card p-8">
          {error && (
            <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label htmlFor="signup-name" className="label">Full name</label>
              <input
                id="signup-name"
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Jane Smith"
                className="input-field"
                autoComplete="name"
                required
              />
            </div>
            <div>
              <label htmlFor="signup-email" className="label">Email address</label>
              <input
                id="signup-email"
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
              <label htmlFor="signup-password" className="label">Password</label>
              <div className="relative">
                <input
                  id="signup-password"
                  type={showPw ? 'text' : 'password'}
                  value={pw}
                  onChange={e => setPw(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pr-10"
                  autoComplete="new-password"
                  required
                />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {pw.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                  <PasswordRule met={rules.length} label="8+ characters" />
                  <PasswordRule met={rules.upper}  label="Uppercase letter" />
                  <PasswordRule met={rules.number} label="Number" />
                </div>
              )}
            </div>
            <div>
              <label htmlFor="signup-confirm" className="label">Confirm password</label>
              <input
                id="signup-confirm"
                type={showPw ? 'text' : 'password'}
                value={cpw}
                onChange={e => setCpw(e.target.value)}
                placeholder="••••••••"
                className="input-field"
                autoComplete="new-password"
                required
              />
              {cpw.length > 0 && !rules.match && (
                <p className="mt-1 text-xs text-red-500">Passwords do not match</p>
              )}
            </div>
            <button
              id="signup-submit"
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-2.5"
            >
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Creating account…</> : 'Create account'}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-600 font-medium hover:text-primary-700">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
