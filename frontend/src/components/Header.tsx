import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.tsx'
import { useShell } from '../hooks/useShell.tsx'
import { Icon } from './ui/Icon.tsx'

const titles: Record<string, string> = {
  '/': 'Overview', '/courses': 'Courses', '/semesters': 'Semesters', '/marks': 'Marks',
  '/attendance': 'Attendance', '/exams': 'Exams', '/assignments': 'Assignments',
  '/planner': 'Planner', '/analytics': 'Analytics', '/documents': 'Documents',
  '/assistant': 'CampusPulse AI', '/students': 'Students', '/enrollments': 'Enrollments',
}

export function Header() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { student, logout } = useAuth()
  const { openSidebar, sidebarOpen } = useShell()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const title = pathname.startsWith('/documents/') && pathname !== '/documents'
    ? 'Document details'
    : (titles[pathname] ?? 'Workspace')

  useEffect(() => {
    document.title = `${title} · CampusPulse`
  }, [title])

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setMenuOpen(false)
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [])

  async function handleLogout() {
    setMenuOpen(false)
    try { await logout() } finally { navigate('/login', { replace: true }) }
  }

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--cp-border)]/80 bg-[color-mix(in_srgb,var(--cp-bg)_88%,white)]/90 backdrop-blur-xl">
      <div className="flex min-h-[4.6rem] items-center justify-between gap-4 px-4 sm:px-6 lg:px-9">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--cp-radius-sm)] border border-[var(--cp-border)] bg-white text-[var(--cp-ink)] transition hover:bg-[var(--cp-brand-wash)] lg:hidden"
            onClick={openSidebar}
            aria-label="Open navigation"
            aria-controls="primary-navigation"
            aria-expanded={sidebarOpen}
          >
            <Icon name="menu" className="h-5 w-5" />
          </button>
          <div className="min-w-0">
            <p className="hidden text-[0.62rem] font-bold uppercase tracking-[0.16em] text-[var(--cp-muted)] sm:block">CampusPulse <span className="px-1 text-[#a4afa8]">/</span> Workspace</p>
            <h1 className="truncate text-[0.94rem] font-semibold tracking-tight text-[var(--cp-ink)] sm:mt-0.5 sm:text-[1.02rem]">{title}</h1>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          {pathname !== '/assistant' ? (
            <Link to="/assistant" className="inline-flex min-h-10 items-center gap-2 rounded-[var(--cp-radius-sm)] bg-[var(--cp-brand)] px-3 text-xs font-semibold text-white transition hover:bg-[var(--cp-brand-soft)] sm:px-4 sm:text-sm">
              <Icon name="spark" className="h-4 w-4 text-[var(--cp-accent)]" />
              <span className="hidden sm:inline">Ask CampusPulse</span>
              <span className="sm:hidden">Ask</span>
            </Link>
          ) : null}
          {student ? (
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                className="flex h-10 items-center gap-2 rounded-[var(--cp-radius-sm)] border border-[var(--cp-border)] bg-white p-1.5 pr-2.5 text-left transition hover:border-[#c4d1c7] sm:gap-3 sm:pr-3"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                aria-label={`Account menu for ${student.full_name}`}
                onClick={() => setMenuOpen((open) => !open)}
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--cp-brand-wash)] text-[0.63rem] font-bold text-[var(--cp-brand)]">
                  {student.full_name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()}
                </span>
                <span className="hidden max-w-32 truncate text-xs font-semibold text-[var(--cp-ink)] sm:block">{student.full_name}</span>
                <span aria-hidden="true" className="hidden text-[0.62rem] text-[var(--cp-muted)] sm:inline">⌄</span>
              </button>
              {menuOpen ? (
                <div role="menu" className="absolute right-0 mt-2 w-60 rounded-[var(--cp-radius)] border border-[var(--cp-border)] bg-white p-2 shadow-[var(--cp-shadow-raised)]">
                  <div className="border-b border-[var(--cp-border)] px-3 py-2.5">
                    <p className="truncate text-sm font-semibold text-[var(--cp-ink)]">{student.full_name}</p>
                    <p className="mt-0.5 truncate text-xs text-[var(--cp-muted)]">{student.email}</p>
                    <p className="mt-1 text-[0.68rem] text-[var(--cp-muted)]">{student.university_id}</p>
                  </div>
                  <button type="button" role="menuitem" className="mt-1 w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium text-[var(--cp-ink)] hover:bg-[var(--cp-brand-wash)]" onClick={() => { setMenuOpen(false); navigate('/marks') }}>View marks</button>
                  <button type="button" role="menuitem" className="w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium text-[#a3322d] hover:bg-[#fcf2f0]" onClick={() => void handleLogout()}><span className="inline-flex items-center gap-2"><Icon name="logout" className="h-4 w-4" />Log out</span></button>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </header>
  )
}
