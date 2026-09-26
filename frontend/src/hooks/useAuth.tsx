import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import {
  currentAccount,
  loginAccount,
  logoutAccount,
  registerAccount,
  storeSession,
} from '../services/auth.ts'
import type { RegisterInput } from '../services/auth.ts'
import { clearToken, getToken } from '../services/session.ts'
import type { Student } from '../types/entities.ts'

type AuthContextValue = {
  student: Student | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (input: RegisterInput) => Promise<void>
  logout: () => Promise<void>
  updateStudent: (student: Student) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [student, setStudent] = useState<Student | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    async function restore() {
      if (!getToken()) {
        if (active) {
          setLoading(false)
        }
        return
      }
      try {
        const profile = await currentAccount()
        if (active) {
          setStudent(profile)
        }
      } catch {
        clearToken()
        if (active) {
          setStudent(null)
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void restore()
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    function handleUnauthorized() {
      setStudent(null)
    }
    window.addEventListener('campuspulse:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('campuspulse:unauthorized', handleUnauthorized)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      student,
      loading,
      async login(email, password) {
        const result = await loginAccount(email, password)
        storeSession(result)
        setStudent(result.student)
      },
      async register(input) {
        const result = await registerAccount(input)
        storeSession(result)
        setStudent(result.student)
      },
      async logout() {
        try {
          await logoutAccount()
        } finally {
          setStudent(null)
        }
      },
      updateStudent(nextStudent) {
        setStudent(nextStudent)
      },
    }),
    [student, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return value
}
