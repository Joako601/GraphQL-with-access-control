import { useState, type FormEvent } from 'react'
import { CircleAlert, Eye, EyeOff, Loader2 } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { login } from '@/lib/api'
import { ApiError } from '@/lib/graphql'
import type { Session } from '@/lib/session'

const PILL_INPUT = 'h-12 rounded-full border-white/10 bg-white/[0.05] px-5 text-base dark:bg-white/[0.05]'

function loginErrorMessage(err: unknown): string {
  // The backend messages are already user-facing Spanish ("Correo o contraseña incorrectos").
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado. Intenta de nuevo.'
}

export function LoginForm({ onLogin }: { onLogin: (session: Session) => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      onLogin(await login(email.trim(), password))
    } catch (err) {
      setError(loginErrorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email" className="sr-only">Correo electrónico</Label>
        <Input id="email" type="email" autoComplete="email" required placeholder="Correo electrónico"
          value={email} onChange={(e) => setEmail(e.target.value)} className={PILL_INPUT} />
      </div>
      <div className="relative">
        <Label htmlFor="password" className="sr-only">Contraseña</Label>
        <Input id="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required
          placeholder="Contraseña" value={password} onChange={(e) => setPassword(e.target.value)}
          className={`${PILL_INPUT} pr-12`} />
        <Button type="button" variant="ghost" size="icon"
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full text-muted-foreground"
          aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          onClick={() => setShowPassword((v) => !v)}>
          {showPassword ? <EyeOff /> : <Eye />}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <CircleAlert />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" disabled={submitting}
        className="mt-6 h-12 w-full rounded-full bg-white text-base text-black hover:bg-white/90">
        {submitting && <Loader2 className="animate-spin" />}
        {submitting ? 'Ingresando…' : 'Continuar'}
      </Button>
    </form>
  )
}
