import type { ButtonHTMLAttributes, ReactNode } from 'react'

const variants = {
  primary: 'bg-[var(--cp-brand)] text-white hover:bg-[var(--cp-brand-soft)]',
  secondary: 'border border-[var(--cp-border)] bg-white text-[var(--cp-ink)] hover:bg-slate-50',
  ghost: 'text-[var(--cp-muted)] hover:bg-slate-100 hover:text-[var(--cp-ink)]',
  danger: 'bg-red-700 text-white hover:bg-red-800',
} as const

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-5 py-3 text-sm',
} as const

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants
  size?: keyof typeof sizes
  children: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition disabled:cursor-not-allowed disabled:opacity-55 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
