import { clearToken, getToken } from './session.ts'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

type RequestOptions = {
  method?: string
  body?: unknown
  auth?: boolean
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers()
  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }
  if (options.auth !== false) {
    const token = getToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiError(0, 'The CampusPulse API is unreachable.')
    }
    throw error
  }

  if (response.status === 204) {
    return undefined as T
  }

  const payload = await readPayload(response)
  if (!response.ok) {
    if (response.status === 401 && options.auth !== false && getToken()) {
      clearToken()
      window.dispatchEvent(new Event('campuspulse:unauthorized'))
    }
    throw new ApiError(response.status, messageFromPayload(response.status, payload))
  }

  return payload as T
}

async function readPayload(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) {
    return null
  }
  try {
    return JSON.parse(text) as unknown
  } catch {
    return null
  }
}

function messageFromPayload(status: number, payload: unknown): string {
  if (status >= 500) {
    return 'Something went wrong. Try again.'
  }
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = payload.detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
            return item.msg.replace(/^Value error,\s*/i, '')
          }
          return ''
        })
        .filter(Boolean)
      if (messages.length > 0) {
        return messages.join(' ')
      }
    }
  }
  if (status === 401) {
    return 'Authentication is required.'
  }
  return 'Request could not be completed.'
}
