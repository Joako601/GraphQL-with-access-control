import { CalendarRange, LogOut } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import type { BalanceState } from '@/hooks/useDashboardData'
import { periodLabel } from './periodLabel'

interface DashboardHeaderProps {
  companyName: string | null
  balance: BalanceState
  onLogout: () => void
}

function PeriodText({ balance }: { balance: BalanceState }) {
  if (balance.status === 'loading') return <Skeleton className="h-4 w-44" />
  if (balance.status === 'error') return <span>Sin datos para mostrar</span>
  return <span>{periodLabel(balance.data.fromDate, balance.data.toDate)}</span>
}

export function DashboardHeader({ companyName, balance, onLogout }: DashboardHeaderProps) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div className="space-y-2">
        <p className="text-sm text-muted-foreground">Dashboard financiero</p>
        {companyName ? (
          <h1 className="font-serif text-4xl leading-none tracking-tight md:text-5xl">{companyName}</h1>
        ) : (
          <Skeleton className="h-10 w-64" />
        )}
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <Badge variant="outline" className="h-6 rounded-full px-3 text-sm">MXN</Badge>
          <span className="flex items-center gap-2">
            <CalendarRange className="size-4" />
            Período consultado: <PeriodText balance={balance} />
          </span>
        </div>
      </div>
      <Button variant="outline" onClick={onLogout} className="h-10 rounded-full px-4">
        <LogOut />
        Cerrar sesión
      </Button>
    </header>
  )
}
