import { useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { useMutation, type QueryState } from '@/hooks/useApiQuery'
import type { CompanyUser } from '@/lib/admin'
import { assignRole, type CatalogEntry } from '@/lib/roles'
import type { AdminContext } from './AdminPage'
import { FormError, NativeSelect } from './parts'

export function UserRole({ user, ctx, catalog, onAssigned }: {
  user: CompanyUser; ctx: AdminContext; catalog: QueryState<CatalogEntry[]>
  onAssigned: (id: string, role: NonNullable<CompanyUser['role']>) => void
}) {
  const [selected, setSelected] = useState('')
  const { pending, error, run, clearError } = useMutation(ctx.onUnauthenticated)
  const roles = catalog.status === 'success' ? catalog.data : []
  const currentId = roles.find(({ code }) => code === user.role?.code)?.id ?? ''
  const roleId = selected || currentId
  const editable = ctx.permissions.includes('roles.write') && user.isActive && !user.isAdmin

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editable || !roleId || roleId === currentId || pending) return
    await run(async () => {
      const role = await assignRole(ctx.token, user.id, roleId)
      onAssigned(user.id, role)
      setSelected('')
      if (user.id === ctx.companyUserId) ctx.reloadSession()
    })
  }

  return (
    <div className="space-y-1.5">
      <p>{user.role?.name ?? <span className="italic text-muted-foreground">Sin rol</span>}</p>
      {editable && roles.length > 0 && (
        <form onSubmit={(event) => void submit(event)} className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <NativeSelect className="h-8 w-auto" aria-label={`Rol de ${user.user.name}`}
              disabled={pending} value={roleId} onChange={(event) => {
                setSelected(event.target.value)
                clearError()
              }}>
              <option value="" disabled>Seleccionar rol</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id} disabled={role.code === 'ADMINISTRADOR'}>{role.name}</option>
              ))}
            </NativeSelect>
            <Button size="sm" type="submit" variant="outline" disabled={pending || !roleId || roleId === currentId}>
              Guardar rol
            </Button>
          </div>
          <FormError message={error} />
        </form>
      )}
    </div>
  )
}
