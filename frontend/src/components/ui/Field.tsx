import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'

type FieldProps = {
  label: string
  hint?: string
  error?: string
}

export function TextField({
  label,
  hint,
  error,
  id,
  className = '',
  ...props
}: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  const fieldId = id ?? props.name
  return (
    <label className="block text-sm font-medium text-slate-700" htmlFor={fieldId}>
      {label}
      <input
        id={fieldId}
        className={`mt-1.5 w-full rounded-xl border border-[var(--cp-border)] bg-white px-3.5 py-2.5 text-sm text-[var(--cp-ink)] transition outline-none focus:border-[var(--cp-brand)] ${className}`}
        {...props}
      />
      {hint ? <span className="mt-1 block text-xs text-[var(--cp-muted)]">{hint}</span> : null}
      {error ? (
        <span className="mt-1 block text-xs text-red-700" role="alert">
          {error}
        </span>
      ) : null}
    </label>
  )
}

export function SelectField({
  label,
  hint,
  error,
  id,
  children,
  className = '',
  ...props
}: FieldProps & SelectHTMLAttributes<HTMLSelectElement>) {
  const fieldId = id ?? props.name
  return (
    <label className="block text-sm font-medium text-slate-700" htmlFor={fieldId}>
      {label}
      <select
        id={fieldId}
        className={`mt-1.5 w-full rounded-xl border border-[var(--cp-border)] bg-white px-3.5 py-2.5 text-sm text-[var(--cp-ink)] transition outline-none focus:border-[var(--cp-brand)] ${className}`}
        {...props}
      >
        {children}
      </select>
      {hint ? <span className="mt-1 block text-xs text-[var(--cp-muted)]">{hint}</span> : null}
      {error ? (
        <span className="mt-1 block text-xs text-red-700" role="alert">
          {error}
        </span>
      ) : null}
    </label>
  )
}

export function TextAreaField({
  label,
  hint,
  error,
  id,
  className = '',
  ...props
}: FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const fieldId = id ?? props.name
  return (
    <label className="block text-sm font-medium text-slate-700" htmlFor={fieldId}>
      {label}
      <textarea
        id={fieldId}
        className={`mt-1.5 w-full rounded-xl border border-[var(--cp-border)] bg-white px-3.5 py-2.5 text-sm text-[var(--cp-ink)] transition outline-none focus:border-[var(--cp-brand)] ${className}`}
        {...props}
      />
      {hint ? <span className="mt-1 block text-xs text-[var(--cp-muted)]">{hint}</span> : null}
      {error ? (
        <span className="mt-1 block text-xs text-red-700" role="alert">
          {error}
        </span>
      ) : null}
    </label>
  )
}
