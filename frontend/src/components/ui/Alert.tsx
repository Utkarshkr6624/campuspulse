type AlertProps = {
  tone?: 'error' | 'info' | 'success'
  children: string
}

const tones = {
  error: 'border-[#efd2ce] bg-[#fcf2f0] text-[#8f312b]',
  info: 'border-[var(--cp-border)] bg-[var(--cp-surface-raised)] text-[var(--cp-ink)]',
  success: 'border-[#cce7d6] bg-[#eef8f1] text-[#176445]',
}

export function Alert({ tone = 'error', children }: AlertProps) {
  return (
    <p className={`rounded-[var(--cp-radius-sm)] border px-4 py-3 text-sm leading-6 ${tones[tone]}`} role="alert">
      {children}
    </p>
  )
}
