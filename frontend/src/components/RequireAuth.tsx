import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.tsx'

export function RequireAuth() {
  const { student, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f3f5f8]">
        <p className="text-sm text-slate-500" role="status">
          Checking your session
        </p>
      </main>
    )
  }

  if (!student) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
