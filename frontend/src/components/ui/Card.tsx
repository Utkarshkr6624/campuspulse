import type { ReactNode } from 'react'

type CardProps = {
  children: ReactNode
  className?: string
  padded?: boolean
}

export function Card({ children, className = '', padded = true }: CardProps) {
  return (
    <div
      className={`rounded-[var(--cp-radius)] border border-[var(--cp-border)] bg-[var(--cp-surface)] shadow-[var(--cp-shadow)] ${
        padded ? 'p-5' : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}

export function CardTitle({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <h2 className={`text-sm font-semibold tracking-wide text-[var(--cp-muted)] uppercase ${className}`}>{children}</h2>
}
