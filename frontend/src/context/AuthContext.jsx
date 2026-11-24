import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import {
  apiRequest,
  clearTokens,
  getAccessToken,
  saveTokens,
} from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // El perfil permite conocer el rol; el JWT por sí solo no lo devuelve en el login.
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(() => Boolean(getAccessToken()))

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
    setIsLoading(false)
  }, [])

  const loadProfile = useCallback(async () => {
    // Consulta el usuario autenticado sin confiar en un ID enviado por el navegador.
    const { data } = await apiRequest('/usuarios/api/me/')
    setUser(data)
    return data
  }, [])

  useEffect(() => {
    // Si la renovación del token falla, api.js avisa para cerrar la sesión en React.
    const handleSessionExpired = () => {
      clearTokens()
      setUser(null)
      setIsLoading(false)
    }

    window.addEventListener('granero:session-expired', handleSessionExpired)
    return () => window.removeEventListener('granero:session-expired', handleSessionExpired)
  }, [])

  useEffect(() => {
    if (!getAccessToken()) {
      return
    }

    let active = true
    // Recupera el perfil remoto al restaurar una sesión persistida.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadProfile()
      .catch(() => {
        if (active && !getAccessToken()) setUser(null)
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [loadProfile])

  const login = useCallback(async (username, password) => {
    // El endpoint devuelve tokens; después se pide el perfil para obtener rol e ID.
    const { data: tokens } = await apiRequest('/api/token/', {
      method: 'POST',
      auth: false,
      body: { username, password },
    })

    saveTokens(tokens)
    try {
      return await loadProfile()
    } catch (error) {
      // No conservar tokens si no se pudo completar la carga de la sesión.
      clearTokens()
      throw error
    }
  }, [loadProfile])

  const value = useMemo(() => ({
    user,
    isLoading,
    isAuthenticated: Boolean(user),
    login,
    logout,
    loadProfile,
  }), [user, isLoading, login, logout, loadProfile])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider.')
  return context
}
