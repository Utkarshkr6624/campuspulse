type AlertProps = {
  tone?: 'error' | 'info' | 'success'
  children: string
}

const tones = {
  error: 'border-red-200 bg-red-50 text-red-800',
  info: 'border-slate-200 bg-slate-50 text-slate-700',
  success: 'border-teal-200 bg-teal-50 text-teal-800',
}

export function Alert({ tone = 'error', children }: AlertProps) {
  return (
    <p className={`rounded-xl border px-4 py-3 text-sm ${tones[tone]}`} role="alert">
      {children}
    </p>
  )
}
