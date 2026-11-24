import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function RequireAuth({ children, roles }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  // Espera a recuperar el perfil antes de decidir a qué ruta puede entrar.
  if (isLoading) return <p role="status">Verificando sesión…</p>
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  // Esta barrera mejora la navegación; el backend también aplica permisos propios.
  if (roles && !roles.includes(user.rol)) {
    return <Navigate to="/catalogo" replace />
  }

  return children
}
