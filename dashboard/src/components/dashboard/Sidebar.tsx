import { FolderTree, Landmark, LayoutDashboard, ShieldCheck, Users, type LucideIcon } from 'lucide-react'
import { routeHref, type Route } from '@/lib/route'
import type { SessionUser } from '@/lib/session'
import { cn } from '@/lib/utils'

interface NavItem { label: string; route: Route; icon: LucideIcon; permission?: string }

// Ambos formatos del menú usan las mismas rutas y permisos.
const NAV_GROUPS: readonly { title: string; items: NavItem[] }[] = [
  {
    title: 'Financiero',
    items: [{ label: 'Resumen', route: { section: 'financiero' }, icon: LayoutDashboard }],
  },
  {
    title: 'Administración',
    items: [
      { label: 'Usuarios', route: { section: 'admin', module: 'usuarios' }, icon: Users },
      { label: 'Cuentas', route: { section: 'admin', module: 'cuentas' }, icon: Landmark },
      { label: 'Conceptos', route: { section: 'admin', module: 'conceptos' }, icon: FolderTree },
      { label: 'Roles y permisos', route: { section: 'admin', module: 'roles' }, icon: ShieldCheck, permission: 'roles.read' },
    ],
  },
]

function isCurrent(item: Route, current: Route): boolean {
  return routeHref(item) === routeHref(current)
}

function NavLink({ item, current, compact = false }: { item: NavItem; current: Route; compact?: boolean }) {
  const active = isCurrent(item.route, current)
  const Icon = item.icon
  return (
    <a href={routeHref(item.route)} aria-current={active ? 'page' : undefined}
      className={cn('flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors',
        compact && 'shrink-0 gap-2 rounded-full border border-white/10 px-3 py-1.5',
        active ? 'bg-white/[0.08] font-medium text-foreground' : 'text-muted-foreground hover:bg-white/[0.04] hover:text-foreground')}>
      <Icon className="size-4" />
      {item.label}
    </a>
  )
}

function visibleItems(items: NavItem[], permissions: string[]) {
  return items.filter(({ permission }) => !permission || permissions.includes(permission))
}

interface NavProps { route: Route; permissions: string[] }

export function Sidebar({ user, route, permissions }: NavProps & { user: SessionUser }) {
  return (
    <aside className="sticky top-0 hidden h-svh w-60 shrink-0 flex-col border-r border-white/[0.06] bg-black/40 p-4 lg:flex">
      <span className="px-3 py-2 text-sm font-medium tracking-[0.2em] text-foreground/80">INGRESOS</span>
      <nav aria-label="Secciones" className="mt-4 space-y-5">
        {NAV_GROUPS.map((group) => (
          <div key={group.title}>
            <p className="px-3 text-xs uppercase tracking-wider text-muted-foreground">{group.title}</p>
            <div className="mt-2 space-y-1">
              {visibleItems(group.items, permissions).map((item) => <NavLink key={item.label} item={item} current={route} />)}
            </div>
          </div>
        ))}
      </nav>
      <div className="mt-auto rounded-xl border border-white/[0.06] p-3">
        <p className="truncate text-sm font-medium">{user.name}</p>
        <p className="truncate text-xs text-muted-foreground">{user.email}</p>
      </div>
    </aside>
  )
}

/** Debajo de lg la barra lateral se oculta: el mismo menú queda arriba, en una fila desplazable. */
export function MobileNav({ route, permissions }: NavProps) {
  return (
    <nav aria-label="Secciones" className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 lg:hidden">
      {NAV_GROUPS.flatMap((group) => visibleItems(group.items, permissions)).map((item) => (
        <NavLink key={item.label} item={item} current={route} compact />
      ))}
    </nav>
  )
}
