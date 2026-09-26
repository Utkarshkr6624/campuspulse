import type { ReactNode } from 'react'

type CardProps = {
  children: ReactNode
  className?: string
  padded?: boolean
}

export function Card({ children, className = '', padded = true }: CardProps) {
  return (
    <div
      className={`cp-panel ${padded ? 'p-5 sm:p-6' : ''} ${className}`}
    >
      {children}
    </div>
  )
}

export function CardTitle({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <h2 className={`text-base font-semibold tracking-tight text-[var(--cp-ink)] ${className}`}>{children}</h2>
}
