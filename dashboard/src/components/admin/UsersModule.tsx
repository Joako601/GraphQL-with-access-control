import { Fragment, useCallback, useState, type FormEvent } from 'react'
import { Loader2, Search, UserPlus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useApiQuery, useMutation } from '@/hooks/useApiQuery'
import { createCompanyUser, deactivateCompanyUser, fetchCompanyUsers, type CompanyUser } from '@/lib/admin'
import { can, countUsers, filterUsers, formatJoinedAt, type StatusFilter } from '@/lib/catalog'
import { cn } from '@/lib/utils'
import type { AdminContext } from './AdminPage'
import {
  CARD, Denied, EmptyState, Field, FIELD, FormError, FormPanel, LoadFailed, ModuleTitle, PRIMARY, SegmentedFilter,
  SourceNote, StatusBadge, TableSkeleton,
} from './parts'

const STATUS_OPTIONS = [
  { value: 'all', label: 'Todos' },
  { value: 'active', label: 'Activos' },
  { value: 'inactive', label: 'Inactivos' },
] as const

function Counts({ users }: { users: CompanyUser[] }) {
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
function DeactivateConfirm({ user, ctx, onDone, onCancel }: {
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

function RowAction({ user, onDeactivate }: { user: CompanyUser; onDeactivate: () => void }) {
  if (!user.isActive) return <span className="text-xs text-muted-foreground">Historial conservado</span>
  if (user.isAdmin) return <span className="text-xs text-muted-foreground">Principal</span>
  return (
    <Button size="sm" variant="outline" className="rounded-full" onClick={onDeactivate}>Desactivar</Button>
  )
}

interface ListProps {
  users: CompanyUser[]; ctx: AdminContext; canWrite: boolean; onChanged: () => void
}

function UsersTable({ users, ctx, canWrite, onChanged }: ListProps) {
  const [confirming, setConfirming] = useState<string | null>(null)
  const columns = canWrite ? 7 : 6
  return (
    <Table className="text-sm">
      <TableHeader>
        <TableRow>
          <TableHead>Nombre</TableHead>
          <TableHead>Correo</TableHead>
          <TableHead>Rol</TableHead>
          <TableHead>Administrador</TableHead>
          <TableHead>Estado</TableHead>
          <TableHead>Ingreso</TableHead>
          {canWrite && <TableHead className="text-right">Acción</TableHead>}
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((u) => (
          <Fragment key={u.id}>
            <TableRow className={cn(!u.isActive && 'text-muted-foreground')}>
              <TableCell className="font-medium">{u.user.name}</TableCell>
              <TableCell>{u.user.email}</TableCell>
              {/* Rol de la membresía (Parcial II), solo lectura esta semana. */}
              <TableCell>{u.role?.name ?? <span className="italic text-muted-foreground">Sin rol</span>}</TableCell>
              <TableCell>{u.isAdmin ? 'Sí' : 'No'}</TableCell>
              <TableCell><StatusBadge active={u.isActive} /></TableCell>
              <TableCell className="whitespace-nowrap">{formatJoinedAt(u.joinedAt)}</TableCell>
              {canWrite && (
                <TableCell className="text-right">
                  <RowAction user={u} onDeactivate={() => setConfirming(u.id)} />
                </TableCell>
              )}
            </TableRow>
            {confirming === u.id && u.isActive && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={columns} className="whitespace-normal">
                  <DeactivateConfirm user={u} ctx={ctx} onCancel={() => setConfirming(null)}
                    onDone={() => { setConfirming(null); onChanged() }} />
                </TableCell>
              </TableRow>
            )}
          </Fragment>
        ))}
      </TableBody>
    </Table>
  )
}

// Debajo de md la tabla de 7 columnas obligaría a desplazarse de lado: cada membresía es una tarjeta.
function UsersCards({ users, ctx, canWrite, onChanged }: ListProps) {
  const [confirming, setConfirming] = useState<string | null>(null)
  return (
    <ul className="divide-y divide-white/[0.06]">
      {users.map((u) => (
        <li key={u.id} className={cn('space-y-2 py-3', !u.isActive && 'text-muted-foreground')}>
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-medium">{u.user.name}</p>
              <p className="truncate text-xs text-muted-foreground">{u.user.email}</p>
            </div>
            <StatusBadge active={u.isActive} />
          </div>
          <p className="text-xs text-muted-foreground">
            Rol: {u.role?.name ?? 'Sin rol'} · Administrador: {u.isAdmin ? 'Sí' : 'No'} · Ingreso: {formatJoinedAt(u.joinedAt)}
          </p>
          {canWrite && confirming !== u.id && <RowAction user={u} onDeactivate={() => setConfirming(u.id)} />}
          {canWrite && confirming === u.id && u.isActive && (
            <DeactivateConfirm user={u} ctx={ctx} onCancel={() => setConfirming(null)}
              onDone={() => { setConfirming(null); onChanged() }} />
          )}
        </li>
      ))}
    </ul>
  )
}

const EMPTY_FORM = { name: '', email: '', password: '' }

function NewUserForm({ ctx, onCreated, onClose }: { ctx: AdminContext; onCreated: () => void; onClose: () => void }) {
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

export function UsersModule({ ctx }: { ctx: AdminContext }) {
  const fetcher = useCallback(() => fetchCompanyUsers(ctx.token, ctx.companyId), [ctx.token, ctx.companyId])
  const { state, reload } = useApiQuery(fetcher, ctx.onUnauthenticated)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<StatusFilter>('all')
  const [formOpen, setFormOpen] = useState(false)
  const canWrite = can(ctx.permissions, 'company.users.write')

  // Sin company.users.write no se dibuja el botón (el API lo rechazaría igual).
  const action = canWrite && !formOpen ? (
    <Button className={PRIMARY} onClick={() => setFormOpen(true)}><UserPlus />Nuevo usuario</Button>
  ) : null

  if (state.status === 'error') {
    return (
      <section className="space-y-5">
        <ModuleTitle title="Usuarios" question="¿Quién pertenece a la empresa?" />
        {state.error.code === 'FORBIDDEN' ? <Denied error={state.error} /> : <LoadFailed error={state.error} onRetry={reload} />}
      </section>
    )
  }

  return (
    <section className="space-y-5">
      <ModuleTitle title="Usuarios" question="¿Quién pertenece a la empresa?" action={action} />
      {state.status === 'success' ? <Counts users={state.data} /> : <TableSkeleton label="Cargando conteos" />}
      {formOpen && canWrite && <NewUserForm ctx={ctx} onCreated={reload} onClose={() => setFormOpen(false)} />}
      <Card className={CARD}>
        <CardContent className="space-y-4 px-5">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-52 flex-1">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input aria-label="Buscar por nombre o correo" placeholder="Buscar por nombre o correo"
                value={search} onChange={(e) => setSearch(e.target.value)} className={cn(FIELD, 'pl-9')} />
            </div>
            <SegmentedFilter label="Estado" options={STATUS_OPTIONS} value={status} onChange={setStatus} />
          </div>
          {state.status === 'loading' && <TableSkeleton label="Cargando usuarios" />}
          {state.status === 'success' && (() => {
            const rows = filterUsers(state.data, search, status)
            if (state.data.length === 0) return <EmptyState>La empresa todavía no tiene usuarios.</EmptyState>
            if (rows.length === 0) return <EmptyState>Ningún usuario coincide con la búsqueda o el filtro.</EmptyState>
            return (
              <>
                <div className="hidden md:block">
                  <UsersTable users={rows} ctx={ctx} canWrite={canWrite} onChanged={reload} />
                </div>
                <div className="md:hidden">
                  <UsersCards users={rows} ctx={ctx} canWrite={canWrite} onChanged={reload} />
                </div>
              </>
            )
          })()}
          <SourceNote>Los datos salen de <code>companyUsers</code> de la empresa de la sesión.</SourceNote>
        </CardContent>
      </Card>
    </section>
  )
}
