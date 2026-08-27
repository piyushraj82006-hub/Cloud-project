import { useState, useCallback } from 'react'
import { STORAGE_KEYS } from '../utils/constants'

interface UseAuthResult {
  token: string | null
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
}

export function useAuth(): UseAuthResult {
  const [token, setToken] = useState<string | null>(() => {
    try {
      return localStorage.getItem(STORAGE_KEYS.TOKEN)
    } catch {
      return null
    }
  })

  const login = useCallback((newToken: string) => {
    try {
      localStorage.setItem(STORAGE_KEYS.TOKEN, newToken)
    } catch {
      // private browsing
    }
    setToken(newToken)
  }, [])

  const logout = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEYS.TOKEN)
    } catch {
      // private browsing
    }
    setToken(null)
  }, [])

  return {
    token,
    isAuthenticated: token !== null,
    login,
    logout,
  }
}
