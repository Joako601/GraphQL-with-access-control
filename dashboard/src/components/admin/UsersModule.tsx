import { Fragment, useCallback, useState } from 'react'
import { Search, UserPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useApiQuery, type QueryState } from '@/hooks/useApiQuery'
import { fetchCompanyUsers, type CompanyUser } from '@/lib/admin'
import { can, filterUsers, formatJoinedAt, type StatusFilter } from '@/lib/catalog'
import { fetchRoles, type CatalogEntry } from '@/lib/roles'
import { cn } from '@/lib/utils'
import type { AdminContext } from './AdminPage'
import { UserRole } from './UserRole'
import { Counts, DeactivateConfirm, NewUserForm } from './UsersPanels'
import {
  CARD, Denied, EmptyState, FIELD, LoadFailed, ModuleTitle, PRIMARY, SegmentedFilter,
  SourceNote, StatusBadge, TableSkeleton,
} from './parts'

const STATUS_OPTIONS = [
  { value: 'all', label: 'Todos' },
  { value: 'active', label: 'Activos' },
  { value: 'inactive', label: 'Inactivos' },
] as const

function RowAction({ user, onDeactivate }: { user: CompanyUser; onDeactivate: () => void }) {
  if (!user.isActive) return <span className="text-xs text-muted-foreground">Historial conservado</span>
  if (user.isAdmin) return <span className="text-xs text-muted-foreground">Principal</span>
  return (
    <Button size="sm" variant="outline" className="rounded-full" onClick={onDeactivate}>Desactivar</Button>
  )
}

interface ListProps {
  users: CompanyUser[]; ctx: AdminContext; canWrite: boolean; onChanged: () => void
  catalog: QueryState<CatalogEntry[]>
  onAssigned: (id: string, role: NonNullable<CompanyUser['role']>) => void
}

function UsersTable({ users, ctx, canWrite, onChanged, catalog, onAssigned }: ListProps) {
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
              <TableCell className="whitespace-normal">
                <UserRole user={u} ctx={ctx} catalog={catalog} onAssigned={onAssigned} />
              </TableCell>
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
function UsersCards({ users, ctx, canWrite, onChanged, catalog, onAssigned }: ListProps) {
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
          <div className="text-xs"><UserRole user={u} ctx={ctx} catalog={catalog} onAssigned={onAssigned} /></div>
          <p className="text-xs text-muted-foreground">
            Administrador: {u.isAdmin ? 'Sí' : 'No'} · Ingreso: {formatJoinedAt(u.joinedAt)}
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

export function UsersModule({ ctx }: { ctx: AdminContext }) {
  const fetcher = useCallback(() => fetchCompanyUsers(ctx.token, ctx.companyId), [ctx.token, ctx.companyId])
  const { state, reload } = useApiQuery(fetcher, ctx.onUnauthenticated)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<StatusFilter>('all')
  const [formOpen, setFormOpen] = useState(false)
  const [assigned, setAssigned] = useState<{
    base: CompanyUser[]; roles: Record<string, NonNullable<CompanyUser['role']>>
  }>()
  const canWrite = can(ctx.permissions, 'company.users.write')
  const canAssign = can(ctx.permissions, 'roles.write')
  const fetchCatalog = useCallback(() => canAssign ? fetchRoles(ctx.token) : Promise.resolve([]), [canAssign, ctx.token])
  const { state: catalog, reload: reloadCatalog } = useApiQuery(fetchCatalog, ctx.onUnauthenticated)
  function onAssigned(id: string, role: NonNullable<CompanyUser['role']>) {
    if (state.status !== 'success') return
    setAssigned((previous) => ({
      base: state.data,
      roles: { ...(previous?.base === state.data ? previous.roles : {}), [id]: role },
    }))
  }

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
          {canAssign && catalog.status === 'error' && <LoadFailed error={catalog.error} onRetry={reloadCatalog} />}
          {canAssign && catalog.status === 'success' && !catalog.data.length && <EmptyState>No hay roles activos.</EmptyState>}
          {state.status === 'loading' && <TableSkeleton label="Cargando usuarios" />}
          {state.status === 'success' && (() => {
            const rows = filterUsers(state.data, search, status).map((user) => ({
              ...user, role: (assigned?.base === state.data ? assigned.roles[user.id] : undefined) ?? user.role,
            }))
            if (state.data.length === 0) return <EmptyState>La empresa todavía no tiene usuarios.</EmptyState>
            if (rows.length === 0) return <EmptyState>Ningún usuario coincide con la búsqueda o el filtro.</EmptyState>
            return (
              <>
                <div className="hidden md:block">
                  <UsersTable users={rows} ctx={ctx} canWrite={canWrite} onChanged={reload} catalog={catalog} onAssigned={onAssigned} />
                </div>
                <div className="md:hidden">
                  <UsersCards users={rows} ctx={ctx} canWrite={canWrite} onChanged={reload} catalog={catalog} onAssigned={onAssigned} />
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
