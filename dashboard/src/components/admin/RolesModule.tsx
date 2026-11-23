import { useCallback, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useApiQuery, useMutation } from '@/hooks/useApiQuery'
import {
  fetchRoleColumn, fetchRoleMatrix, previewRolePermissions, setRolePermissions,
  type RoleColumn, type RolePreview, type RoleUpdate,
} from '@/lib/roles'
import { cn } from '@/lib/utils'
import type { AdminContext } from './AdminPage'
import { CARD, Denied, EmptyState, FormError, LoadFailed, ModuleTitle, PRIMARY, TableSkeleton } from './parts'

type Matrix = Awaited<ReturnType<typeof fetchRoleMatrix>>
interface Draft { role: RoleColumn['role']; permissionIds: string[] }

function Preview({ plan }: { plan: RolePreview }) {
  return (
    <dl className="grid gap-3 border-t border-white/10 pt-3 text-sm sm:grid-cols-4" aria-label="Vista previa">
      <div><dt>Se activa</dt><dd className="text-emerald-300">{plan.toActivate.map(({ code }) => code).join(', ') || 'Ninguno'}</dd></div>
      <div><dt>Se desactiva</dt><dd className="text-amber-300">{plan.toDeactivate.map(({ code }) => code).join(', ') || 'Ninguno'}</dd></div>
      <div><dt>Sin cambio</dt><dd>{plan.unchanged.length}</dd></div>
      <div><dt>Total final</dt><dd>{plan.finalCount}</dd></div>
    </dl>
  )
}

function RoleMatrix({ matrix, ctx }: { matrix: Matrix; ctx: AdminContext }) {
  const [updated, setUpdated] = useState<Record<string, RoleColumn>>({})
  const [draft, setDraft] = useState<Draft | null>(null)
  const [plan, setPlan] = useState<RolePreview | null>(null)
  const [result, setResult] = useState<RoleUpdate | null>(null)
  const [needsReload, setNeedsReload] = useState(false)
  const { run, pending, error, clearError } = useMutation(ctx.onUnauthenticated)
  const writable = ctx.permissions.includes('roles.write')

  function edit(column: RoleColumn, id?: string) {
    const before = draft?.permissionIds ?? column.permissionIds
    const permissionIds = id === undefined ? before
      : before.includes(id) ? before.filter((value) => value !== id) : [...before, id]
    setDraft({ role: column.role, permissionIds })
    setPlan(null)
    setResult(null)
    clearError()
  }

  async function readColumn(role: Draft['role']) {
    const column = await fetchRoleColumn(ctx.token, role, matrix.activeIds)
    setUpdated((previous) => ({ ...previous, [role.id]: column }))
    setDraft(null)
    setNeedsReload(false)
  }

  async function preview() {
    if (!draft || pending || needsReload || !writable) return
    const input = { roleId: draft.role.id, permissionIds: draft.permissionIds }
    await run(async () => setPlan(await previewRolePermissions(ctx.token, input)))
  }

  async function save() {
    if (!draft || !plan || pending || needsReload || !writable) return
    const input = { roleId: draft.role.id, permissionIds: draft.permissionIds }
    await run(async () => {
      setResult(await setRolePermissions(ctx.token, input))
      setPlan(null)
      setNeedsReload(true)
      await readColumn(draft.role)
    })
  }

  return (
    <Card className={CARD}>
      <CardContent className="space-y-4 px-3 sm:px-5">
        {!writable && <p className="text-sm text-muted-foreground">Solo lectura. Se requiere roles.write para guardar.</p>}
        {result && <p role="status" className="text-sm text-emerald-300">
          {result.changed ? 'Columna guardada' : 'Sin cambios'} · changed: {String(result.changed)} · {result.finalCount} permisos activos
        </p>}
        {writable && draft && (
          <section aria-label={`Edición de ${draft.role.name}`} className="space-y-3 rounded-xl border border-white/10 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="mr-auto font-medium">{draft.role.name}</h3>
              {needsReload ? (
                <Button variant="outline" disabled={pending} onClick={() => void run(() => readColumn(draft.role))}>
                  Volver a leer la columna
                </Button>
              ) : (
                <>
                  <Button variant="ghost" disabled={pending} onClick={() => {
                    setDraft(null); setPlan(null); clearError()
                  }}>Cancelar</Button>
                  <Button variant="outline" disabled={pending} onClick={() => void preview()}>Vista previa</Button>
                  <Button className={PRIMARY} disabled={pending || !plan} onClick={() => void save()}>Guardar columna</Button>
                </>
              )}
            </div>
            {plan && <Preview plan={plan} />}
            <FormError message={error} />
          </section>
        )}
        <Table aria-label="Matriz de roles y permisos" className="min-w-[620px]">
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Permiso</TableHead>
              {matrix.columns.map((column) => {
                const { role } = column
                return (
                  <TableHead key={role.id} scope="col" className="h-auto py-2 text-center">
                    {role.name}
                    <code className="block text-xs text-muted-foreground">{role.code}</code>
                    {role.code === 'ADMINISTRADOR' ? (
                      <span className="block text-xs text-muted-foreground">Solo lectura</span>
                    ) : writable && (
                      <Button size="xs" variant="ghost" aria-label={`Editar ${role.name}`}
                        disabled={Boolean(draft) || pending} onClick={() => edit(updated[role.id] ?? column)}>
                        Editar
                      </Button>
                    )}
                  </TableHead>
                )
              })}
            </TableRow>
          </TableHeader>
          {matrix.groups.map(({ name, permissions }) => (
            <tbody key={name} className="border-t border-white/10">
              <TableRow className="bg-white/[0.04]">
                <TableHead scope="rowgroup" colSpan={matrix.columns.length + 1} className="h-auto py-1 text-xs">{name}</TableHead>
              </TableRow>
              {permissions.map((permission) => (
                <TableRow key={permission.id}>
                  <TableHead scope="row" className="h-auto py-1.5">
                    {permission.name}
                    <code className="block text-xs text-muted-foreground">{permission.code}</code>
                  </TableHead>
                  {matrix.columns.map((initial) => {
                    const column = updated[initial.role.id] ?? initial
                    const selected = draft?.role.id === column.role.id
                    const enabled = writable && column.role.code !== 'ADMINISTRADOR'
                      && !pending && !needsReload && (!draft || selected)
                    const active = (selected ? draft.permissionIds : column.permissionIds).includes(permission.id)
                    return (
                      <TableCell key={column.role.id} className={cn('text-center', selected && 'bg-white/[0.05]')}>
                        <label className="inline-flex items-center gap-2">
                          {writable && column.role.code !== 'ADMINISTRADOR' && (
                            <input type="checkbox" checked={active} disabled={!enabled}
                              aria-label={`${column.role.name} · ${permission.name}`}
                              className="size-4 accent-emerald-400"
                              onChange={() => edit(column, permission.id)} />
                          )}
                          <span className={active ? 'text-emerald-300' : 'text-muted-foreground'}>{active ? 'Sí' : 'No'}</span>
                        </label>
                      </TableCell>
                    )
                  })}
                </TableRow>
              ))}
            </tbody>
          ))}
        </Table>
      </CardContent>
    </Card>
  )
}

export function RolesModule({ ctx }: { ctx: AdminContext }) {
  const fetcher = useCallback(() => fetchRoleMatrix(ctx.token), [ctx.token])
  const { state, reload } = useApiQuery(fetcher, ctx.onUnauthenticated)
  return (
    <section className="space-y-5">
      <ModuleTitle title="Roles y permisos" question="El catálogo es compartido. Cada cambio aplica a todas las empresas." />
      {state.status === 'loading' && <TableSkeleton label="Cargando catálogo de roles y permisos" />}
      {state.status === 'error' && (state.error.code === 'FORBIDDEN'
        ? <Denied error={state.error} /> : <LoadFailed error={state.error} onRetry={reload} />)}
      {state.status === 'success' && (state.data.columns.length
        ? <RoleMatrix matrix={state.data} ctx={ctx} />
        : <EmptyState>El catálogo de roles y permisos no está cargado.</EmptyState>)}
    </section>
  )
}
