import type { FormEvent, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from './ui/Alert.tsx'
import { Button } from './ui/Button.tsx'
import { TextField } from './ui/Field.tsx'

type AuthCardProps = {
  title: string
  description: string
  error: string | null
  submitting: boolean
  submitLabel: string
  footer: ReactNode
  children: ReactNode
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

export function AuthCard({
  title,
  description,
  error,
  submitting,
  submitLabel,
  footer,
  children,
  onSubmit,
}: AuthCardProps) {
  return (
    <main className="min-h-screen bg-[var(--cp-bg)] p-3 sm:p-6 lg:p-8">
      <div className="mx-auto grid min-h-[calc(100vh-1.5rem)] max-w-6xl overflow-hidden rounded-[1.5rem] border border-[var(--cp-border)] bg-white shadow-[var(--cp-shadow-raised)] sm:min-h-[calc(100vh-3rem)] lg:grid-cols-[1.05fr_0.95fr]">
        <aside className="relative hidden flex-col justify-between overflow-hidden bg-[var(--cp-brand)] p-10 text-white lg:flex xl:p-14">
          <div className="relative z-10 flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--cp-accent)] text-xs font-black tracking-[-0.08em] text-[var(--cp-brand)]">CP</span>
            <div><p className="text-sm font-semibold">CampusPulse</p><p className="text-xs text-white/75">Academic workspace</p></div>
          </div>
          <div className="relative z-10 max-w-lg pb-8">
            <p className="cp-kicker !text-[var(--cp-accent)]">Academic life, in focus</p>
            <h2 className="mt-4 text-4xl font-semibold leading-[1.08] tracking-[-0.055em] xl:text-5xl">One place to understand your progress.</h2>
            <p className="mt-5 max-w-md text-sm leading-7 text-white/65">Bring semesters, courses, marks, and plans together in a clear personal workspace.</p>
          </div>
          <p className="relative z-10 text-xs text-white/75">A calmer view of the work you’re putting in.</p>
          <div aria-hidden="true" className="pointer-events-none absolute -bottom-20 -right-24 h-80 w-80 rounded-full border border-white/10" />
          <div aria-hidden="true" className="pointer-events-none absolute -bottom-12 -right-16 h-64 w-64 rounded-full border border-white/10" />
        </aside>
        <div className="flex items-center justify-center px-5 py-10 sm:px-10 lg:px-12">
          <div className="w-full max-w-md cp-fade-up">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--cp-brand)] text-xs font-black tracking-[-0.08em] text-[var(--cp-accent)]">CP</span>
              <div><p className="text-sm font-semibold text-[var(--cp-ink)]">CampusPulse</p><p className="text-xs text-[var(--cp-muted)]">Academic workspace</p></div>
            </div>
            <p className="cp-kicker">Welcome</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.045em] text-[var(--cp-ink)]">{title}</h1>
            <p className="mt-2 text-sm leading-6 text-[var(--cp-muted)]">{description}</p>
            <form className="mt-7 space-y-4" onSubmit={onSubmit}>
              {children}
              {error ? <Alert>{error}</Alert> : null}
              <Button className="w-full" size="lg" type="submit" disabled={submitting}>
                {submitting ? 'Please wait' : submitLabel}
              </Button>
            </form>
            <p className="mt-5 text-sm text-[var(--cp-muted)]">{footer}</p>
          </div>
        </div>
      </div>
    </main>
  )
}

export function AuthField({
  label,
  name,
  type,
  value,
  autoComplete,
  onChange,
}: {
  label: string
  name: string
  type: string
  value: string
  autoComplete: string
  onChange: (value: string) => void
}) {
  return (
    <TextField
      label={label}
      name={name}
      type={type}
      value={value}
      autoComplete={autoComplete}
      required
      onChange={(event) => onChange(event.target.value)}
    />
  )
}

export function AuthLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link className="font-semibold text-[var(--cp-brand)] underline decoration-[var(--cp-accent)] underline-offset-2" to={to}>
      {children}
    </Link>
  )
}
