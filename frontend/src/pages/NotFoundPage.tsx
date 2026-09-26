import { Link } from 'react-router-dom'
import { EmptyState } from '../components/ui/EmptyState.tsx'

export function NotFoundPage() {
  return (
    <EmptyState title="Page not found" message="This page is not part of CampusPulse.">
      <Link className="mt-4 inline-block text-sm font-semibold text-[var(--cp-brand)] underline" to="/">
        Back to dashboard
      </Link>
    </EmptyState>
  )
}
