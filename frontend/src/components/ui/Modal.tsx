import { useEffect, useRef } from 'react'
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
  const previousFocus = useRef<HTMLElement | null>(null)
  const onCloseRef = useRef(onClose)

  useEffect(() => {
    onCloseRef.current = onClose
  }, [onClose])

  useEffect(() => {
    if (!open) {
      return
    }
    previousFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onCloseRef.current()
      }
      if (event.key === 'Tab') {
        const dialog = document.getElementById('cp-modal-dialog')
        const focusable = dialog?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
        )
        if (!focusable?.length) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.setTimeout(() => document.getElementById('cp-modal-dialog')?.querySelector<HTMLElement>('button, input, select, textarea, a[href]')?.focus(), 0)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previous
      // Return keyboard focus to the element that opened the dialog.
      const trigger = previousFocus.current
      window.setTimeout(() => trigger?.focus(), 0)
    }
  }, [open])

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
        id="cp-modal-dialog"
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
