import type { ButtonHTMLAttributes, ReactNode } from 'react'

const variants = {
  primary: 'bg-[var(--cp-brand)] text-white shadow-sm hover:bg-[var(--cp-brand-soft)] active:translate-y-px',
  secondary: 'border border-[var(--cp-border)] bg-white text-[var(--cp-ink)] hover:border-[#c4d1c7] hover:bg-[var(--cp-surface-raised)] active:translate-y-px',
  ghost: 'text-[var(--cp-muted)] hover:bg-[var(--cp-brand-wash)] hover:text-[var(--cp-brand)]',
  danger: 'bg-[#a8332c] text-white hover:bg-[#8f2a25] active:translate-y-px',
} as const

const sizes = {
  sm: 'min-h-9 px-3 text-xs',
  md: 'min-h-10 px-4 text-sm',
  lg: 'min-h-12 px-5 text-sm',
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
      className={`inline-flex items-center justify-center gap-2 rounded-[var(--cp-radius-sm)] font-semibold transition duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-55 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
