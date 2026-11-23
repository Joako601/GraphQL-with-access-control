import { LogOut } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import type { QueryState } from '@/hooks/useApiQuery'
import type { Me } from '@/lib/admin'
import { ApiError } from '@/lib/graphql'
import type { AdminModule } from '@/lib/route'
import type { Session } from '@/lib/session'
import { AccountsModule } from './AccountsModule'
import { ConceptsModule } from './ConceptsModule'
import { Denied, LoadFailed } from './parts'
import { RolesModule } from './RolesModule'
import { UsersModule } from './UsersModule'

/** Lo que cada módulo necesita de la sesión. La empresa y los permisos salen de `me`, no del navegador. */
export interface AdminContext {
  token: string
  companyId: string
  companyUserId: string
  permissions: string[]
  reloadSession: () => void
  onUnauthenticated: () => void
}

interface AdminPageProps {
  session: Session
  module: AdminModule
  state: QueryState<Me>
  reload: () => void
  onLogout: () => void
  onUnauthenticated: () => void
}

function AdminHeader({ me, onLogout }: { me: Me | null; onLogout: () => void }) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div className="space-y-2">
        <p className="text-sm text-muted-foreground">Dashboard administrativo</p>
        {me ? (
          <h1 className="font-serif text-4xl leading-none tracking-tight md:text-5xl">{me.company.name}</h1>
        ) : (
          <Skeleton className="h-10 w-64" />
        )}
        {me && (
          <p className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            Sesión de {me.user.name} ·
            <Badge variant="outline" className="h-6 rounded-full px-3 text-sm">
              Rol: {me.role?.name ?? 'sin rol'}
            </Badge>
          </p>
        )}
      </div>
      <Button variant="outline" onClick={onLogout} className="h-10 rounded-full px-4">
        <LogOut />
        Cerrar sesión
      </Button>
    </header>
  )
}

export function AdminPage({ session, module, state, reload, onLogout, onUnauthenticated }: AdminPageProps) {
  const me = state.status === 'success' ? state.data : null
  const ctx: AdminContext | null = me && {
    token: session.token, companyId: me.companyId, companyUserId: me.companyUserId,
    permissions: me.permissions, reloadSession: reload, onUnauthenticated,
  }

  return (
    <>
      <AdminHeader me={me} onLogout={onLogout} />
      {state.status === 'error' && <LoadFailed error={state.error} onRetry={() => reload()} />}
      {state.status === 'loading' && <Skeleton className="h-96 rounded-2xl" />}
      {/* key: al cambiar de módulo se monta de nuevo y vuelve a consultar el API. */}
      {ctx && module === 'usuarios' && <UsersModule key="u" ctx={ctx} />}
      {ctx && module === 'cuentas' && <AccountsModule key="c" ctx={ctx} />}
      {ctx && module === 'conceptos' && <ConceptsModule key="k" ctx={ctx} />}
      {ctx && module === 'roles' && (ctx.permissions.includes('roles.read')
        ? <RolesModule key="r" ctx={ctx} />
        : <Denied error={new ApiError('Se requiere el permiso roles.read.', 'FORBIDDEN')} />)}
    </>
  )
}
