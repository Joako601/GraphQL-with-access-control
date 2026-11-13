import { useDashboardData, type BalanceState } from '@/hooks/useDashboardData'
import { isZero } from '@/lib/format'
import { DEFAULT_PERIOD } from '@/lib/period'
import type { Session } from '@/lib/session'
import { AccountsTable } from './AccountsTable'
import { DashboardHeader } from './DashboardHeader'
import { KpiCards } from './KpiCards'
import { PeriodControls } from './PeriodControls'
import { periodLabel } from './periodLabel'
import { RiskPanel } from './RiskPanel'
import { Sidebar } from './Sidebar'
import { AccessDenied, DashboardSkeleton, NoMovementsNote, RequestError } from './States'

interface DashboardPageProps {
  session: Session
  onLogout: () => void
  onUnauthenticated: () => void
}

function BalanceContent({ state, onRetry }: { state: BalanceState; onRetry: () => void }) {
  if (state.status === 'loading') return <DashboardSkeleton />
  if (state.status === 'error' && state.error.code === 'FORBIDDEN') return <AccessDenied />
  if (state.status === 'error') return <RequestError error={state.error} onRetry={onRetry} />

  const { data } = state
  // Labels use the dates the server answered for, never the current input values.
  const period = periodLabel(data.fromDate, data.toDate)
  const noMovements = isZero(data.totalIncome) && isZero(data.totalExpense)

  return (
    <div className="space-y-6">
      <section aria-labelledby="kpi-title" className="space-y-3">
        <h2 id="kpi-title" className="text-sm text-muted-foreground">
          Indicadores generales · MXN · {period}
        </h2>
        {noMovements && <NoMovementsNote period={period} />}
        <KpiCards data={data} />
      </section>
      <RiskPanel data={data} period={period} />
      <AccountsTable accounts={data.accounts} period={period} />
    </div>
  )
}

export function DashboardPage({ session, onLogout, onUnauthenticated }: DashboardPageProps) {
  const { companyName, balance, load, retry } = useDashboardData(session.token, DEFAULT_PERIOD, onUnauthenticated)

  return (
    <div className="flex min-h-svh bg-background">
      <Sidebar user={session.user} />
      <main className="mx-auto w-full max-w-7xl min-w-0 space-y-6 p-4 md:p-8">
        <DashboardHeader companyName={companyName} balance={balance} onLogout={onLogout} />
        <PeriodControls loading={balance.status === 'loading'} onSubmit={(period) => void load(period)} />
        <BalanceContent state={balance} onRetry={() => void retry()} />
      </main>
    </div>
  )
}
