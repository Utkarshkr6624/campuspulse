import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { Button } from './Button.tsx'

type ModalProps = {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
  footer?: ReactNode
}

export function Modal({ open, title, children, onClose, footer }: ModalProps) {
  useEffect(() => {
    if (!open) {
      return
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previous
    }
  }, [open, onClose])

  if (!open) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center" role="presentation">
      <button
        aria-label="Close dialog"
        className="absolute inset-0 bg-slate-900/40"
        type="button"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="cp-modal-title"
        className="relative z-10 w-full max-w-lg rounded-2xl border border-[var(--cp-border)] bg-white p-5 shadow-[var(--cp-shadow)] cp-fade-up"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 id="cp-modal-title" className="text-lg font-semibold text-[var(--cp-ink)]">
            {title}
          </h2>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            Close
          </Button>
        </div>
        <div>{children}</div>
        {footer ? <div className="mt-5 flex flex-wrap justify-end gap-2">{footer}</div> : null}
      </div>
    </div>
  )
}
