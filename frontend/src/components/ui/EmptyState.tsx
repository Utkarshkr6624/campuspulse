import type { ReactNode } from 'react'
import { Button } from './Button.tsx'
import { Card } from './Card.tsx'

type EmptyStateProps = {
  title: string
  message: string
  actionLabel?: string
  onAction?: () => void
  children?: ReactNode
}

export function EmptyState({ title, message, actionLabel, onAction, children }: EmptyStateProps) {
  return (
    <Card className="border-dashed bg-[var(--cp-surface-raised)] px-6 py-10 text-center sm:text-left">
      <span aria-hidden="true" className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-[var(--cp-brand-wash)] text-[var(--cp-brand)] sm:mx-0">↗</span>
      <h2 className="text-base font-semibold tracking-tight text-[var(--cp-ink)]">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-[var(--cp-muted)] sm:mx-0">{message}</p>
      {children}
      {actionLabel && onAction ? (
        <div className="mt-5">
          <Button onClick={onAction}>{actionLabel}</Button>
        </div>
      ) : null}
    </Card>
  )
}
