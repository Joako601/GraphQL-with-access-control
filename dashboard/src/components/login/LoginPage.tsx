import { Info } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { Session } from '@/lib/session'
import { LoginForm } from './LoginForm'

interface LoginPageProps {
  notice: string | null
  onLogin: (session: Session) => void
}

function BackgroundBlobs() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute -left-32 top-10 size-[28rem] rounded-full bg-white/[0.11] blur-3xl" />
      <div className="absolute bottom-[-6rem] left-1/3 size-[22rem] rounded-full bg-white/[0.08] blur-3xl" />
      <div className="absolute right-[12%] top-[14%] size-40 rounded-full bg-white/[0.12] blur-2xl" />
      <div className="absolute bottom-[10%] right-[8%] size-64 rounded-full bg-white/[0.07] blur-3xl" />
    </div>
  )
}

export function LoginPage({ notice, onLogin }: LoginPageProps) {
  return (
    <main className="relative flex min-h-svh items-center justify-center bg-background px-4 py-16">
      <BackgroundBlobs />
      <span className="absolute left-6 top-5 text-sm font-medium tracking-[0.2em] text-foreground/80">
        INGRESOS
      </span>

      <Card className="relative w-full max-w-sm gap-6 rounded-3xl border border-white/10 bg-white/[0.03] py-10 ring-0 backdrop-blur-xl">
        <CardHeader className="justify-items-center px-8 text-center">
          <CardTitle className="font-serif text-4xl font-normal tracking-tight">Bienvenido</CardTitle>
          <CardDescription>Inicia sesión para ver el dashboard financiero</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 px-8">
          {notice && (
            <Alert>
              <Info />
              <AlertDescription className="text-foreground/90">{notice}</AlertDescription>
            </Alert>
          )}
          <LoginForm onLogin={onLogin} />
        </CardContent>
      </Card>
    </main>
  )
}
