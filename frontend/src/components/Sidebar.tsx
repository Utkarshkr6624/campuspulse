import { NavLink } from 'react-router-dom'
import { useShell } from '../hooks/useShell.tsx'

const links = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/courses', label: 'Courses', end: false },
  { to: '/marks', label: 'Marks', end: false },
  { to: '/attendance', label: 'Attendance', end: false },
  { to: '/exams', label: 'Exams', end: false },
  { to: '/assignments', label: 'Assignments', end: false },
  { to: '/planner', label: 'Planner', end: false },
  { to: '/analytics', label: 'Analytics', end: false },
  { to: '/documents', label: 'Documents', end: false },
]

export function Sidebar() {
  const { sidebarOpen, closeSidebar } = useShell()

  return (
    <>
      <button
        type="button"
        aria-label="Close navigation"
        className={`fixed inset-0 z-30 bg-slate-900/40 transition lg:hidden ${
          sidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
        onClick={closeSidebar}
      />
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-white/10 bg-[var(--cp-brand)] text-white transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 px-5 py-6">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--cp-accent)] text-sm font-bold text-[var(--cp-brand)]">
            CP
          </span>
          <div>
            <p className="text-sm font-semibold tracking-wide">CampusPulse</p>
            <p className="text-xs text-slate-300">Academic workspace</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3 pb-6" aria-label="Primary">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              onClick={closeSidebar}
              className={({ isActive }) =>
                `flex items-center rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? 'bg-white/12 text-white shadow-[inset_3px_0_0_0_var(--cp-accent)]'
                    : 'text-slate-300 hover:bg-white/6 hover:text-white'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 px-5 py-4 text-xs text-slate-400">
          Phase 7 · University knowledge
        </div>
      </aside>
    </>
  )
}
