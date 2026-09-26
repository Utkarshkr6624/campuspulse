import type { Student } from '../types/entities.ts'
import { request } from './http.ts'
import { clearToken, setToken } from './session.ts'

export type RegisterInput = {
  full_name: string
  email: string
  university_id: string
  password: string
}

export type AuthResult = {
  access_token: string
  token_type: string
  student: Student
}

export function registerAccount(input: RegisterInput): Promise<AuthResult> {
  return request<AuthResult>('/api/auth/register', { method: 'POST', body: input, auth: false })
}

export function loginAccount(email: string, password: string): Promise<AuthResult> {
  return request<AuthResult>('/api/auth/login', {
    method: 'POST',
    body: { email, password },
    auth: false,
  })
}

export function currentAccount(): Promise<Student> {
  return request<Student>('/api/auth/me')
}

export async function logoutAccount(): Promise<void> {
  try {
    await request<void>('/api/auth/logout', { method: 'POST' })
  } finally {
    clearToken()
  }
}

export function storeSession(result: AuthResult): void {
  setToken(result.access_token)
}
