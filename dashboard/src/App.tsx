import { useCallback, useState, type ReactNode } from 'react'
import { AdminPage } from '@/components/admin/AdminPage'
import { DashboardPage } from '@/components/dashboard/DashboardPage'
import { MobileNav, Sidebar } from '@/components/dashboard/Sidebar'
import { LoginPage } from '@/components/login/LoginPage'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useHashRoute } from '@/hooks/useHashRoute'
import type { Route } from '@/lib/route'
import { clearSession, readSession, saveSession, type Session } from '@/lib/session'

const EXPIRED_MESSAGE = 'Tu sesión expiró o el token no es válido. Inicia sesión de nuevo.'

/** Una sola aplicación: mismo login, mismo menú; cambia la sección (financiero o administración). */
function AppShell({ session, route, children }: { session: Session; route: Route; children: ReactNode }) {
  return (
    <div className="flex min-h-svh bg-background">
      <Sidebar user={session.user} route={route} />
      <main className="mx-auto w-full max-w-7xl min-w-0 space-y-6 p-4 md:p-8">
        <MobileNav route={route} />
        {children}
      </main>
    </div>
  )
}

export default function App() {
  const [session, setSession] = useState<Session | null>(readSession)
  const [notice, setNotice] = useState<string | null>(null)
  const route = useHashRoute()

  const handleLogin = useCallback((newSession: Session) => {
    saveSession(newSession)
    setNotice(null)
    setSession(newSession)
  }, [])

  // Cerrar sesión borra el token y vuelve al login, igual que en la actividad 1.
  const endSession = useCallback((message: string | null) => {
    clearSession()
    setNotice(message)
    setSession(null)
  }, [])

  const handleExpired = useCallback(() => endSession(EXPIRED_MESSAGE), [endSession])
  const handleLogout = useCallback(() => endSession(null), [endSession])

  return (
    <TooltipProvider>
      {session ? (
        <AppShell session={session} route={route}>
          {route.section === 'admin' ? (
            <AdminPage session={session} module={route.module} onLogout={handleLogout}
              onUnauthenticated={handleExpired} />
          ) : (
            <DashboardPage session={session} onLogout={handleLogout} onUnauthenticated={handleExpired} />
          )}
        </AppShell>
      ) : (
        <LoginPage notice={notice} onLogin={handleLogin} />
      )}
      <Toaster theme="dark" position="top-right" />
    </TooltipProvider>
  )
}
