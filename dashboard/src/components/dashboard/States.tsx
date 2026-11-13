import { CalendarOff, CircleAlert, RefreshCw, ShieldX, WifiOff } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { ApiError } from '@/lib/graphql'

const CARD = 'rounded-2xl border border-white/[0.06] py-5 ring-0'

/** FORBIDDEN: explain the missing permissions and show no numbers at all (not even zeros). */
export function AccessDenied() {
  return (
    <Card className={CARD}>
      <CardContent className="flex flex-col items-center gap-3 px-5 py-10 text-center">
        <ShieldX className="size-10 text-red-400" />
        <h2 className="text-2xl font-semibold">Acceso denegado</h2>
        <p className="max-w-md text-muted-foreground">
          Tu usuario no tiene permisos de lectura de cuentas y movimientos, por lo que no puede ver los
          indicadores financieros de la empresa. Solicita acceso a un administrador.
        </p>
      </CardContent>
    </Card>
  )
}

export function RequestError({ error, onRetry }: { error: ApiError; onRetry: () => void }) {
  if (error.code === 'BAD_USER_INPUT') {
    return (
      <Alert variant="destructive">
        <CircleAlert />
        <AlertTitle>No se pudo consultar el período</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    )
  }
  const isNetwork = error.code === 'NETWORK'
  const Icon = isNetwork ? WifiOff : CircleAlert
  return (
    <Card className={CARD}>
      <CardContent className="flex flex-col items-center gap-3 px-5 py-10 text-center">
        <Icon className="size-10 text-muted-foreground" />
        <h2 className="text-xl font-semibold">{isNetwork ? 'Sin conexión con el servidor' : 'Ocurrió un error'}</h2>
        <p className="max-w-md text-muted-foreground">{error.message}</p>
        <Button variant="outline" onClick={onRetry} className="mt-2 h-10 rounded-full px-5">
          <RefreshCw />
          Reintentar
        </Button>
      </CardContent>
    </Card>
  )
}

export function NoMovementsNote({ period }: { period: string }) {
  return (
    <Alert>
      <CalendarOff />
      <AlertTitle>Sin movimientos</AlertTitle>
      <AlertDescription>No hubo ingresos ni egresos en el período {period}.</AlertDescription>
    </Alert>
  )
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Cargando indicadores">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-36 rounded-2xl" />)}
      </div>
      <Skeleton className="h-28 rounded-2xl" />
      <Skeleton className="h-64 rounded-2xl" />
    </div>
  )
}
