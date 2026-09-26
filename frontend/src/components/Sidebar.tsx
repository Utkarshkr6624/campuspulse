import { NavLink } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../hooks/useAuth.tsx'
import { useShell } from '../hooks/useShell.tsx'
import { Icon } from './ui/Icon.tsx'
import type { IconName } from './ui/Icon.tsx'

const groups: Array<{ label: string; links: Array<{ to: string; label: string; icon: IconName; end?: boolean }> }> = [
  { label: 'Workspace', links: [
    { to: '/', label: 'Overview', icon: 'grid', end: true },
    { to: '/analytics', label: 'Analytics', icon: 'chart' },
    { to: '/assistant', label: 'CampusPulse AI', icon: 'spark' },
  ] },
  { label: 'Academics', links: [
    { to: '/semesters', label: 'Semesters', icon: 'calendar' },
    { to: '/courses', label: 'Courses', icon: 'book' },
    { to: '/marks', label: 'Marks', icon: 'pencil' },
    { to: '/attendance', label: 'Attendance', icon: 'check' },
  ] },
  { label: 'Planning', links: [
    { to: '/exams', label: 'Exams', icon: 'calendar' },
    { to: '/assignments', label: 'Assignments', icon: 'file' },
    { to: '/planner', label: 'Planner', icon: 'grid' },
    { to: '/goals', label: 'Goals & scenarios', icon: 'chart' },
    { to: '/documents', label: 'Documents', icon: 'book' },
  ] },
]

export function Sidebar() {
  const { student } = useAuth()
  const { sidebarOpen, closeSidebar } = useShell()
  const asideRef = useRef<HTMLElement>(null)
  const [mobileViewport, setMobileViewport] = useState(false)
  const navGroups = student?.role === 'ADMIN'
    ? [...groups, { label: 'Administration', links: [
      { to: '/students', label: 'Students', icon: 'users' as const },
      { to: '/enrollments', label: 'Enrollments', icon: 'check' as const },
    ] }]
    : groups

  useEffect(() => {
    const query = window.matchMedia('(max-width: 1023px)')
    const update = () => setMobileViewport(query.matches)
    update()
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (!sidebarOpen) return
    asideRef.current?.querySelector<HTMLElement>('a')?.focus()
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        closeSidebar()
        document.querySelector<HTMLButtonElement>('[aria-label="Open navigation"]')?.focus()
      }
    }
    document.addEventListener('keydown', closeOnEscape)
    return () => document.removeEventListener('keydown', closeOnEscape)
  }, [sidebarOpen, closeSidebar])

  return (
    <>
      <button
        type="button"
        aria-label="Close navigation"
        aria-hidden={!sidebarOpen}
        tabIndex={sidebarOpen ? 0 : -1}
        className={`fixed inset-0 z-30 bg-[#101d18]/45 backdrop-blur-[2px] transition-opacity duration-200 lg:hidden ${sidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'}`}
        onClick={closeSidebar}
      />
      <aside
        ref={asideRef}
        id="primary-navigation"
        aria-label="Primary navigation"
        aria-hidden={mobileViewport && !sidebarOpen}
        inert={mobileViewport && !sidebarOpen ? true : undefined}
        className={`fixed inset-y-0 left-0 z-40 flex w-[17rem] flex-col border-r border-white/10 bg-[var(--cp-brand)] text-white transition-transform duration-200 lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex min-h-[5.25rem] items-center gap-3 px-6">
          <span className="flex h-10 w-10 items-center justify-center rounded-[0.8rem] bg-[var(--cp-accent)] text-[0.8rem] font-black tracking-[-0.08em] text-[var(--cp-brand)]">CP</span>
          <div className="min-w-0">
            <p className="text-[0.95rem] font-semibold tracking-tight">CampusPulse</p>
            <p className="mt-0.5 text-[0.69rem] text-white/55">Academic workspace</p>
          </div>
          <button type="button" className="ml-auto rounded-lg p-2 text-white/65 hover:bg-white/10 hover:text-white lg:hidden" onClick={closeSidebar} aria-label="Close navigation">
            <Icon name="close" className="h-5 w-5" />
          </button>
        </div>

        <nav className="cp-scrollbar flex-1 space-y-6 overflow-y-auto px-3 pb-4 pt-3" aria-label="Primary">
          {navGroups.map((group) => (
            <section key={group.label}>
              <h2 className="mb-2 px-3 text-[0.63rem] font-bold uppercase tracking-[0.16em] text-white/40">{group.label}</h2>
              <ul className="space-y-1">
                {group.links.map((link) => (
                  <li key={link.to}>
                    <NavLink
                      to={link.to}
                      end={link.end}
                      onClick={closeSidebar}
                      className={({ isActive }) => `group flex min-h-10 items-center gap-3 rounded-[0.7rem] px-3 text-[0.83rem] font-medium transition-colors duration-150 ${isActive ? 'bg-white/12 text-white shadow-[inset_2px_0_0_var(--cp-accent)]' : 'text-white/65 hover:bg-white/[0.07] hover:text-white'}`}
                    >
                      <Icon name={link.icon} className="h-[1.05rem] w-[1.05rem] shrink-0 opacity-90" />
                      <span>{link.label}</span>
                      {link.to === '/assistant' ? <span className="ml-auto rounded-full bg-[var(--cp-accent)]/15 px-2 py-0.5 text-[0.58rem] font-bold uppercase tracking-wide text-[var(--cp-accent)]">Guide</span> : null}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>

        <div className="border-t border-white/10 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-[0.65rem] font-semibold text-[var(--cp-accent)]">{student?.full_name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase() || 'CP'}</span>
            <div className="min-w-0">
              <p className="truncate text-xs font-medium text-white/90">{student?.full_name ?? 'CampusPulse'}</p>
              <p className="mt-0.5 text-[0.65rem] text-white/45">Personal academic space</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
