type ProgressBarProps = {
  value: number | null
  label?: string
}

export function ProgressBar({ value, label }: ProgressBarProps) {
  const safe = value === null ? 0 : Math.max(0, Math.min(100, value))
  const tone =
    value === null ? 'bg-slate-200' : safe >= 85 ? 'bg-teal-600' : safe >= 75 ? 'bg-[var(--cp-brand)]' : 'bg-amber-500'

  return (
    <div>
      {label ? (
        <div className="mb-2 flex items-center justify-between gap-3 text-sm">
          <span className="text-[var(--cp-muted)]">{label}</span>
          <span className="font-semibold text-[var(--cp-ink)]">{value === null ? '—' : `${value}%`}</span>
        </div>
      ) : null}
      <div
        className="h-2.5 overflow-hidden rounded-full bg-slate-100"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value === null ? undefined : safe}
        aria-label={label ?? 'Progress'}
      >
        <div className={`h-full rounded-full transition-all ${tone}`} style={{ width: `${safe}%` }} />
      </div>
    </div>
  )
}
