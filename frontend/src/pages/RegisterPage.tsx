import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { AuthCard, AuthField, AuthLink } from '../components/AuthCard.tsx'
import { useAuth } from '../hooks/useAuth.tsx'
import { ApiError } from '../services/http.ts'

export function RegisterPage() {
  const { student, loading, register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [universityId, setUniversityId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    document.title = 'Create account · CampusPulse'
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
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setSubmitting(true)
    try {
      await register({
        full_name: fullName,
        email,
        university_id: universityId,
        password,
      })
      navigate('/', { replace: true })
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Registration failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthCard
      title="Create an account"
      description="Register with your university email and student ID."
      error={error}
      submitting={submitting}
      submitLabel="Create account"
      onSubmit={handleSubmit}
      footer={
        <>
          Already registered? <AuthLink to="/login">Sign in</AuthLink>
        </>
      }
    >
      <AuthField
        label="Full name"
        name="full_name"
        type="text"
        value={fullName}
        autoComplete="name"
        onChange={setFullName}
      />
      <AuthField label="Email" name="email" type="email" value={email} autoComplete="email" onChange={setEmail} />
      <AuthField
        label="University ID"
        name="university_id"
        type="text"
        value={universityId}
        autoComplete="off"
        onChange={setUniversityId}
      />
      <AuthField
        label="Password"
        name="password"
        type="password"
        value={password}
        autoComplete="new-password"
        onChange={setPassword}
      />
    </AuthCard>
  )
}
