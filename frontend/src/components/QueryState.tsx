import type { ReactNode } from 'react'
import { Alert } from './ui/Alert.tsx'
import { EmptyState } from './ui/EmptyState.tsx'
import { LoadingState } from './ui/LoadingState.tsx'

type QueryStateProps<T> = {
  data: T[] | null
  error: string | null
  loading: boolean
  loadingLabel: string
  emptyTitle: string
  emptyMessage: string
  emptyActionLabel?: string
  onEmptyAction?: () => void
  children: (data: T[]) => ReactNode
}

export function QueryState<T>({
  data,
  error,
  loading,
  loadingLabel,
  emptyTitle,
  emptyMessage,
  emptyActionLabel,
  onEmptyAction,
  children,
}: QueryStateProps<T>) {
  if (loading) {
    return <LoadingState label={loadingLabel} />
  }

  if (error) {
    return <Alert>{error}</Alert>
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        message={emptyMessage}
        actionLabel={emptyActionLabel}
        onAction={onEmptyAction}
      />
    )
  }

  return children(data)
}
