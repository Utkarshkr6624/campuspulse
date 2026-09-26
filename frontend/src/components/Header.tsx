import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.tsx'
import { useShell } from '../hooks/useShell.tsx'
import { Button } from './ui/Button.tsx'

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/courses': 'Courses',
  '/semesters': 'Semesters',
  '/marks': 'Marks',
  '/attendance': 'Attendance',
  '/exams': 'Exams',
  '/assignments': 'Assignments',
  '/planner': 'Planner',
  '/analytics': 'Analytics',
  '/documents': 'Documents',
  '/assistant': 'AI Assistant',
  '/students': 'Students',
  '/enrollments': 'Enrollments',
}

function greetingForHour(hour: number): string {
  if (hour < 12) {
    return 'Good morning'
  }
  if (hour < 17) {
    return 'Good afternoon'
  }
  return 'Good evening'
}

export function Header() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { student, logout } = useAuth()
  const { openSidebar } = useShell()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const title =
    pathname.startsWith('/documents/') && pathname !== '/documents'
      ? 'Document'
      : (titles[pathname] ?? 'Page not found')
  const now = new Date()
  const greeting = greetingForHour(now.getHours())
  const dateLabel = now.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })

  useEffect(() => {
    document.title = `${title} · CampusPulse`
  }, [title])

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [])

  async function handleLogout() {
    setMenuOpen(false)
    try {
      await logout()
    } finally {
      navigate('/login', { replace: true })
    }
  }

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--cp-border)] bg-[color-mix(in_srgb,var(--cp-surface)_92%,transparent)] backdrop-blur">
      <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <Button variant="secondary" size="sm" className="lg:hidden" onClick={openSidebar} aria-label="Open navigation">
            Menu
          </Button>
          <div className="min-w-0">
            <p className="truncate text-xs font-medium tracking-wide text-[var(--cp-muted)] uppercase">{title}</p>
            <h1 className="truncate text-lg font-semibold text-[var(--cp-ink)] sm:text-xl">
              {student ? `${greeting}, ${student.full_name.split(' ')[0]}` : title}
            </h1>
            <p className="truncate text-sm text-[var(--cp-muted)]">{dateLabel}</p>
          </div>
        </div>

        {student ? (
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              className="flex items-center gap-3 rounded-xl border border-[var(--cp-border)] bg-white px-3 py-2 text-left transition hover:bg-slate-50"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--cp-brand)] text-xs font-bold text-white">
                {student.full_name
                  .split(' ')
                  .map((part) => part[0])
                  .join('')
                  .slice(0, 2)
                  .toUpperCase()}
              </span>
              <span className="hidden sm:block">
                <span className="block text-sm font-semibold text-[var(--cp-ink)]">{student.full_name}</span>
                <span className="block text-xs text-[var(--cp-muted)]">{student.university_id}</span>
              </span>
            </button>
            {menuOpen ? (
              <div
                role="menu"
                className="absolute right-0 mt-2 w-56 rounded-xl border border-[var(--cp-border)] bg-white p-2 shadow-[var(--cp-shadow)]"
              >
                <div className="border-b border-[var(--cp-border)] px-3 py-2">
                  <p className="text-sm font-semibold text-[var(--cp-ink)]">{student.full_name}</p>
                  <p className="truncate text-xs text-[var(--cp-muted)]">{student.email}</p>
                </div>
                <button
                  type="button"
                  role="menuitem"
                  className="mt-1 w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-50"
                  onClick={() => {
                    setMenuOpen(false)
                    navigate('/marks')
                  }}
                >
                  View marks
                </button>
                <button
                  type="button"
                  role="menuitem"
                  className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-50"
                  onClick={() => void handleLogout()}
                >
                  Log out
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </header>
  )
}
