import { useCallback, useState } from 'react'
import { DashboardPage } from '@/components/dashboard/DashboardPage'
import { LoginPage } from '@/components/login/LoginPage'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { clearSession, readSession, saveSession, type Session } from '@/lib/session'

const EXPIRED_MESSAGE = 'Tu sesión expiró o el token no es válido. Inicia sesión de nuevo.'

export default function App() {
  const [session, setSession] = useState<Session | null>(readSession)
  const [notice, setNotice] = useState<string | null>(null)

  const handleLogin = useCallback((newSession: Session) => {
    saveSession(newSession)
    setNotice(null)
    setSession(newSession)
  }, [])

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
        <DashboardPage session={session} onLogout={handleLogout} onUnauthenticated={handleExpired} />
      ) : (
        <LoginPage notice={notice} onLogin={handleLogin} />
      )}
      <Toaster theme="dark" position="top-right" />
    </TooltipProvider>
  )
}
