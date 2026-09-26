import type { FormEvent, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from './ui/Alert.tsx'
import { Button } from './ui/Button.tsx'
import { Card } from './ui/Card.tsx'
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
    <main className="flex min-h-screen items-center justify-center bg-[var(--cp-bg)] px-4 py-10">
      <div className="w-full max-w-md cp-fade-up">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--cp-brand)] text-sm font-bold text-[var(--cp-accent)]">
            CP
          </span>
          <div>
            <p className="text-base font-semibold text-[var(--cp-ink)]">CampusPulse</p>
            <p className="text-sm text-[var(--cp-muted)]">University academic workspace</p>
          </div>
        </div>
        <Card className="p-6">
          <h1 className="text-xl font-semibold text-[var(--cp-ink)]">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-[var(--cp-muted)]">{description}</p>
          <form className="mt-6 space-y-4" onSubmit={onSubmit}>
            {children}
            {error ? <Alert>{error}</Alert> : null}
            <Button className="w-full" type="submit" disabled={submitting}>
              {submitting ? 'Please wait' : submitLabel}
            </Button>
          </form>
          <p className="mt-4 text-sm text-[var(--cp-muted)]">{footer}</p>
        </Card>
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
