import type { ReactNode } from 'react'

const tones = {
  neutral: 'bg-[#eef1ed] text-[#53625a]',
  brand: 'bg-[var(--cp-brand-wash)] text-[var(--cp-brand)]',
  accent: 'bg-[#f6efd9] text-[#7d5a12]',
  success: 'bg-[#e8f4ec] text-[#176445]',
  danger: 'bg-[#f9eae7] text-[#a3322d]',
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
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[0.68rem] font-semibold leading-none tracking-wide ${tones[tone]} ${className}`}>
      {children}
    </span>
  )
}
