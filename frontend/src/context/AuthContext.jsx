import { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore session on mount
  useEffect(() => {
    const token = localStorage.getItem('ssa_token')
    if (!token) { setLoading(false); return }
    authApi.me()
      .then(r => setUser(r.data))
      .catch(() => localStorage.removeItem('ssa_token'))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    const { data } = await authApi.login({ email, password })
    localStorage.setItem('ssa_token', data.access_token)
    setUser(data.user)
    return data.user
  }

  const signup = async (name, email, password, confirmPassword) => {
    const { data } = await authApi.signup({ name, email, password, confirm_password: confirmPassword })
    localStorage.setItem('ssa_token', data.access_token)
    setUser(data.user)
    return data.user
  }

  const logout = async () => {
    try { await authApi.logout() } catch (_) {}
    localStorage.removeItem('ssa_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
