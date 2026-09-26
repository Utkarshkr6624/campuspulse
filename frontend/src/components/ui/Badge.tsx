import type { ReactNode } from 'react'

const tones = {
  neutral: 'bg-slate-100 text-slate-700',
  brand: 'bg-[color-mix(in_srgb,var(--cp-brand)_10%,white)] text-[var(--cp-brand)]',
  accent: 'bg-[color-mix(in_srgb,var(--cp-accent)_18%,white)] text-[#7a6110]',
  success: 'bg-teal-50 text-teal-800',
  danger: 'bg-red-50 text-red-700',
} as const

export function Badge({
  children,
  tone = 'neutral',
  className = '',
}: {
  children: ReactNode
  tone?: keyof typeof tones
  className?: string
}) {
  return (
    <span className={`inline-flex items-center rounded-lg px-2 py-1 text-xs font-semibold ${tones[tone]} ${className}`}>
      {children}
    </span>
  )
}
