import { LayoutDashboard } from 'lucide-react'
import type { SessionUser } from '@/lib/session'

export function Sidebar({ user }: { user: SessionUser }) {
  return (
    <aside className="sticky top-0 hidden h-svh w-60 shrink-0 flex-col border-r border-white/[0.06] bg-black/40 p-4 lg:flex">
      <span className="px-3 py-2 text-sm font-medium tracking-[0.2em] text-foreground/80">INGRESOS</span>
      <p className="mt-6 px-3 text-xs uppercase tracking-wider text-muted-foreground">Plataforma</p>
      <nav className="mt-2">
        <span aria-current="page"
          className="flex items-center gap-3 rounded-xl bg-white/[0.06] px-3 py-2 text-sm font-medium">
          <LayoutDashboard className="size-4" />
          Dashboard
        </span>
      </nav>
      <div className="mt-auto rounded-xl border border-white/[0.06] p-3">
        <p className="truncate text-sm font-medium">{user.name}</p>
        <p className="truncate text-xs text-muted-foreground">{user.email}</p>
      </div>
    </aside>
  )
}
