import { Outlet } from 'react-router-dom'
import { Header } from '../components/Header.tsx'
import { Sidebar } from '../components/Sidebar.tsx'
import { ShellProvider } from '../hooks/useShell.tsx'

export function AppLayout() {
  return (
    <ShellProvider>
      <div className="cp-app-canvas text-[var(--cp-ink)]">
        <Sidebar />
        <div className="min-h-screen lg:pl-[17rem]">
          <Header />
          <main className="px-4 py-6 sm:px-6 lg:px-9 lg:py-8">
            <div className="cp-page cp-fade-up">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </ShellProvider>
  )
}
