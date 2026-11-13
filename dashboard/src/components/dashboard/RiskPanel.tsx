import { ShieldAlert, ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import type { GeneralBalance } from '@/lib/api'
import { cn } from '@/lib/utils'

const PILL = 'h-7 rounded-full px-3 text-sm'

export function RiskPanel({ data, period }: { data: GeneralBalance; period: string }) {
  // Names come from the same response; the count itself is the server's accountsInRed.
  const redAccounts = data.accounts.filter((account) => account.isInRed)
  const Icon = data.isInRed || data.accountsInRed > 0 ? ShieldAlert : ShieldCheck

  return (
    <Card className="rounded-2xl border border-white/[0.06] py-5 ring-0">
      <CardHeader className="px-5">
        <CardTitle className="flex items-center gap-2">
          <Icon className="size-4" />
          Estado de riesgo
        </CardTitle>
        <CardDescription>Saldos finales negativos al cierre del período {period}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5 px-5 md:flex-row md:items-center">
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">¿General en rojo?</span>
          {data.isInRed ? (
            <Badge variant="destructive" className={PILL}>Sí</Badge>
          ) : (
            <Badge className={cn(PILL, 'bg-success/15 text-success')}>No</Badge>
          )}
        </div>
        <Separator orientation="vertical" className="hidden h-8 md:block" />
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Cuentas en rojo:</span>
          <span className={cn('text-2xl font-semibold tabular-nums', data.accountsInRed > 0 && 'text-red-400')}>
            {data.accountsInRed}
          </span>
          {redAccounts.length === 0 && <span className="text-sm text-muted-foreground">Ninguna</span>}
          {redAccounts.map((account) => (
            <Badge key={account.accountId} variant="destructive" className={PILL}>
              {account.accountName}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
