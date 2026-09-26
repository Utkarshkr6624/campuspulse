import { useEffect, useState } from 'react'

function toErrorMessage(error: unknown): string {
  if (error instanceof TypeError) {
    return 'The CampusPulse API is unreachable.'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong.'
}

export function useApiList<T>(loader: () => Promise<T[]>) {
  const [data, setData] = useState<T[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    loader()
      .then((items) => {
        if (active) {
          setData(items)
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(toErrorMessage(caught))
        }
      })

    return () => {
      active = false
    }
  }, [loader])

  return {
    data,
    error,
    loading: data === null && error === null,
  }
}
