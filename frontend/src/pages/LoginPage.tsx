import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { AuthCard, AuthField, AuthLink } from '../components/AuthCard.tsx'
import { useAuth } from '../hooks/useAuth.tsx'
import { ApiError } from '../services/http.ts'

export function LoginPage() {
  const { student, loading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    document.title = 'Sign in · CampusPulse'
  }, [])

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f3f5f8]">
        <p className="text-sm text-slate-500" role="status">
          Checking your session
        </p>
      </main>
    )
  }

  if (student) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      const state = location.state as { from?: string } | null
      navigate(state?.from && state.from !== '/login' ? state.from : '/', { replace: true })
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Sign in failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthCard
      title="Sign in"
      description="Use your university email and password to open CampusPulse."
      error={error}
      submitting={submitting}
      submitLabel="Sign in"
      onSubmit={handleSubmit}
      footer={
        <>
          New to CampusPulse? <AuthLink to="/register">Create an account</AuthLink>
        </>
      }
    >
      <AuthField label="Email" name="email" type="email" value={email} autoComplete="email" onChange={setEmail} />
      <AuthField
        label="Password"
        name="password"
        type="password"
        value={password}
        autoComplete="current-password"
        onChange={setPassword}
      />
    </AuthCard>
  )
}
