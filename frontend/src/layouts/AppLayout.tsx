import { Outlet } from 'react-router-dom'
import { Header } from '../components/Header.tsx'
import { Sidebar } from '../components/Sidebar.tsx'
import { ShellProvider } from '../hooks/useShell.tsx'

export function AppLayout() {
  return (
    <ShellProvider>
      <div className="min-h-screen bg-[var(--cp-bg)] text-[var(--cp-ink)]">
        <Sidebar />
        <div className="lg:pl-72">
          <Header />
          <main className="px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            <div className="mx-auto max-w-6xl cp-fade-up">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </ShellProvider>
  )
}
