import type { ComponentProps, ReactNode } from 'react'
import { CircleAlert, RefreshCw, ShieldX, X } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import type { ApiError } from '@/lib/graphql'
import { cn } from '@/lib/utils'

export const CARD = 'rounded-2xl border border-white/[0.06] py-5 ring-0'
export const FIELD = 'h-10 rounded-xl border-white/10 bg-white/[0.04] px-3 dark:bg-white/[0.04]'
export const PRIMARY = 'h-10 rounded-full bg-white px-5 text-black hover:bg-white/90'

/** Una pregunta por pantalla: el título y la pregunta que responde. */
export function ModuleTitle({ title, question, action }: { title: string; question: string; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
        <p className="text-sm text-muted-foreground">{question}</p>
      </div>
      {action}
    </div>
  )
}

/** Activo/inactivo se distingue con texto y color, no solo con color. */
export function StatusBadge({ active, feminine = false }: { active: boolean; feminine?: boolean }) {
  const text = active ? (feminine ? 'Activa' : 'Activo') : (feminine ? 'Inactiva' : 'Inactivo')
  return (
    <Badge variant="outline" className={cn('rounded-full',
      active ? 'border-emerald-500/30 text-emerald-300' : 'border-white/15 bg-white/[0.04] text-muted-foreground')}>
      {text}
    </Badge>
  )
}

interface Option<T extends string> { value: T; label: string }

/** Filtro de botones sobre la lista ya cargada (no hace otra consulta). */
export function SegmentedFilter<T extends string>({ label, options, value, onChange }: {
  label: string; options: readonly Option<T>[]; value: T; onChange: (value: T) => void
}) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap gap-1.5">
      {options.map((option) => (
        <Button key={option.value} type="button" size="sm" variant="outline" aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn('h-8 rounded-full px-3', value === option.value && 'border-white/40 bg-white/10 text-foreground')}>
          {option.label}
        </Button>
      ))}
    </div>
  )
}

export function Field({ id, label, hint, children }: { id: string; label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

export function NativeSelect({ className, ...props }: ComponentProps<'select'>) {
  return (
    <select {...props}
      className={cn(FIELD, 'w-full border text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50 [&>option]:bg-neutral-900', className)} />
  )
}

export function TextArea({ className, ...props }: ComponentProps<'textarea'>) {
  return (
    <textarea {...props}
      className={cn('min-h-20 w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-3 focus-visible:ring-ring/50', className)} />
  )
}

/** Error del API leído en la interfaz (correo duplicado, concepto ya asignado…), no solo en la consola. */
export function FormError({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <Alert variant="destructive">
      <CircleAlert />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  )
}

export function Denied({ error }: { error: ApiError }) {
  return (
    <Card className={CARD}>
      <CardContent className="flex flex-col items-center gap-3 px-5 py-10 text-center">
        <ShieldX className="size-9 text-red-400" />
        <h3 className="text-xl font-semibold">Acceso denegado</h3>
        <p className="max-w-md text-sm text-muted-foreground">{error.message}</p>
      </CardContent>
    </Card>
  )
}

export function LoadFailed({ error, onRetry }: { error: ApiError; onRetry: () => void }) {
  return (
    <Card className={CARD}>
      <CardContent className="flex flex-col items-center gap-3 px-5 py-10 text-center">
        <CircleAlert className="size-9 text-muted-foreground" />
        <h3 className="text-xl font-semibold">
          {error.code === 'NETWORK' ? 'Sin conexión con el servidor' : 'No se pudo cargar la tabla'}
        </h3>
        <p className="max-w-md text-sm text-muted-foreground">{error.message}</p>
        <Button variant="outline" onClick={onRetry} className="mt-2 h-10 rounded-full px-5">
          <RefreshCw />
          Reintentar
        </Button>
      </CardContent>
    </Card>
  )
}

export function TableSkeleton({ label }: { label: string }) {
  return (
    <div className="space-y-2" aria-busy="true" aria-label={label}>
      {Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-11 rounded-xl" />)}
    </div>
  )
}

/** Estado vacío: la tabla dice qué falta, no queda un recuadro en blanco. */
export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-xl border border-dashed border-white/10 p-8 text-center text-sm text-muted-foreground">
      {children}
    </p>
  )
}

export function SourceNote({ children }: { children: ReactNode }) {
  return <p className="text-xs text-muted-foreground">{children}</p>
}

/** Formulario de alta a todo el ancho, sobre la tabla: así la tabla nunca se queda sin espacio. */
export function FormPanel({ title, note, onClose, children }: {
  title: string; note?: string; onClose: () => void; children: ReactNode
}) {
  return (
    <Card className={cn(CARD, 'border-white/15')}>
      <CardHeader className="flex flex-row items-start justify-between gap-3 px-5">
        <div>
          <CardTitle>{title}</CardTitle>
          {note && <CardDescription>{note}</CardDescription>}
        </div>
        <Button variant="ghost" size="icon-sm" aria-label="Cerrar formulario" onClick={onClose}><X /></Button>
      </CardHeader>
      <CardContent className="px-5">{children}</CardContent>
    </Card>
  )
}
