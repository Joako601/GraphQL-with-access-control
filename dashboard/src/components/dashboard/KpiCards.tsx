import type { ReactNode } from 'react'
import { Info } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { GeneralBalance } from '@/lib/api'
import { formatDate, isNegative } from '@/lib/format'
import { cn } from '@/lib/utils'
import { balanceClass, profitClass } from './amountTone'
import { Money } from './Money'

interface KpiCardProps {
  label: string
  hint: string
  value: string
  valueClass?: string
  footer: ReactNode
}

function KpiCard({ label, hint, value, valueClass, footer }: KpiCardProps) {
  return (
    <Card className="gap-3 rounded-2xl border border-white/[0.06] py-5 ring-0">
      <CardHeader className="px-5">
        <CardTitle className="flex items-center gap-1.5 text-sm font-normal text-muted-foreground">
          {label}
          <Tooltip>
            <TooltipTrigger aria-label={`Qué es ${label}`}>
              <Info className="size-3.5" />
            </TooltipTrigger>
            <TooltipContent>{hint}</TooltipContent>
          </Tooltip>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 px-5">
        <Money value={value} className={cn('block text-3xl font-semibold tracking-tight', valueClass)} />
        <div className="min-h-6 text-sm text-muted-foreground">{footer}</div>
      </CardContent>
    </Card>
  )
}

const POSITIVE_CHIP = 'rounded-full bg-success/15 text-success'

function ProfitFooter({ profit }: { profit: string }) {
  if (!isNegative(profit)) return <Badge className={POSITIVE_CHIP}>Ganancia en el período</Badge>
  return (
    <Badge variant="outline" className="rounded-full border-warning/30 text-warning">
      Pérdida en el período
    </Badge>
  )
}

function ClosingFooter({ data }: { data: GeneralBalance }) {
  if (data.isInRed) return <Badge variant="destructive" className="rounded-full">En rojo</Badge>
  return <Badge className={POSITIVE_CHIP}>Sin números rojos</Badge>
}

export function KpiCards({ data }: { data: GeneralBalance }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <KpiCard
        label="Saldo inicial"
        hint="openingBalance: dinero al inicio del período"
        value={data.openingBalance}
        valueClass={balanceClass(data.openingBalance)}
        footer={`Al inicio del ${formatDate(data.fromDate)}`}
      />
      <KpiCard label="Ingresos" hint="totalIncome: entradas en el período" value={data.totalIncome} footer="Entradas del período" />
      <KpiCard label="Egresos" hint="totalExpense: salidas en el período" value={data.totalExpense} footer="Salidas del período" />
      <KpiCard
        label="Profit"
        hint="profit: ingresos − egresos del período"
        value={data.profit}
        valueClass={profitClass(data.profit)}
        footer={<ProfitFooter profit={data.profit} />}
      />
      <KpiCard
        label="Saldo final"
        hint="closingBalance: saldo inicial + profit"
        value={data.closingBalance}
        valueClass={balanceClass(data.closingBalance)}
        footer={<ClosingFooter data={data} />}
      />
    </div>
  )
}
