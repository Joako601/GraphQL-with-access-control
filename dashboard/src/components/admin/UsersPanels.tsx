import { useState, type FormEvent } from 'react'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useMutation } from '@/hooks/useApiQuery'
import { createCompanyUser, deactivateCompanyUser, type CompanyUser } from '@/lib/admin'
import { countUsers } from '@/lib/catalog'
import { cn } from '@/lib/utils'
import type { AdminContext } from './AdminPage'
import { CARD, Field, FIELD, FormError, FormPanel, PRIMARY } from './parts'

export function Counts({ users }: { users: CompanyUser[] }) {
  const counts = countUsers(users)
  const tiles = [
    { label: 'Usuarios activos', value: counts.active, warn: false },
    // 0 o 1. Más de uno es un error de datos del Parcial I: se muestra en ámbar, no se oculta.
    { label: 'Administrador principal', value: counts.admins, warn: counts.admins > 1 },
    { label: 'Inactivos', value: counts.inactive, warn: false },
  ]
  return (
    <div className="grid grid-cols-3 gap-3">
      {tiles.map((tile) => (
        <Card key={tile.label} className={cn(CARD, 'py-4', tile.warn && 'border-amber-500/40')}>
          <CardContent className="px-4 sm:px-5">
            <p className="text-xs text-muted-foreground sm:text-sm">{tile.label}</p>
            {/* Conteos de personas, no importes: sin etiqueta MXN. */}
            <p className={cn('mt-1 text-3xl font-semibold tabular-nums', tile.warn && 'text-amber-300')}>{tile.value}</p>
            {tile.warn && <p className="mt-1 text-xs text-amber-300">Hay más de un administrador: revisar datos.</p>}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

/** Desactivar es una baja lógica: el texto lo dice, no hay "borrar para siempre". */
export function DeactivateConfirm({ user, ctx, onDone, onCancel }: {
  user: CompanyUser; ctx: AdminContext; onDone: () => void; onCancel: () => void
}) {
  const { run, pending, error } = useMutation(ctx.onUnauthenticated)

  async function confirm() {
    if (await run(() => deactivateCompanyUser(ctx.token, user.id))) {
      toast.success(`${user.user.name} ya no opera en la empresa`, { description: 'Su historial se conserva.' })
      onDone()
    }
  }
  return (
    <div className="space-y-2 rounded-xl border border-white/10 bg-white/[0.03] p-3">
      <p className="text-sm">
        <b>{user.user.name}</b> deja de operar en la empresa y ya no podrá iniciar sesión en ella. No se borra:
        la fila y su historial se conservan con estado inactivo.
      </p>
      <div className="flex gap-2">
        <Button size="sm" variant="destructive" className="rounded-full" disabled={pending} onClick={() => void confirm()}>
          {pending && <Loader2 className="animate-spin" />}
          Confirmar desactivación
        </Button>
        <Button size="sm" variant="ghost" className="rounded-full" disabled={pending} onClick={onCancel}>Cancelar</Button>
      </div>
      <FormError message={error} />
    </div>
  )
}

const EMPTY_FORM = { name: '', email: '', password: '' }

export function NewUserForm({ ctx, onCreated, onClose }: { ctx: AdminContext; onCreated: () => void; onClose: () => void }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const { run, pending, error } = useMutation(ctx.onUnauthenticated)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const name = form.name.trim()
    if (await run(() => createCompanyUser(ctx.token, ctx.companyId, { ...form, name, email: form.email.trim() }))) {
      toast.success(`${name} se agregó a la empresa`)
      setForm(EMPTY_FORM) // la contraseña no se queda en la pantalla
      onCreated()
    }
  }

  return (
    <FormPanel title="Nuevo usuario" onClose={onClose}
      note="Entra con el rol Consulta. El administrador principal ya existe (createCompanyAdmin) y no se crea desde aquí.">
      <form onSubmit={(e) => void submit(e)} className="space-y-4">
        <div className="grid gap-4 md:grid-cols-3">
          <Field id="nu-name" label="Nombre">
            <Input id="nu-name" required value={form.name} className={FIELD}
              onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field id="nu-email" label="Correo">
            <Input id="nu-email" type="email" required autoComplete="off" value={form.email} className={FIELD}
              onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>
          {/* La contraseña solo existe aquí y en la mutación; la respuesta no la devuelve y ninguna tabla la muestra. */}
          <Field id="nu-password" label="Contraseña" hint="Mínimo 8 caracteres.">
            <Input id="nu-password" type="password" required minLength={8} autoComplete="new-password"
              value={form.password} className={FIELD} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </Field>
        </div>
        <FormError message={error} />
        <Button type="submit" disabled={pending} className={PRIMARY}>
          {pending && <Loader2 className="animate-spin" />}
          Guardar
        </Button>
      </form>
    </FormPanel>
  )
}
