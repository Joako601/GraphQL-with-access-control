import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { AccountBalance } from '@/lib/api'
import { cn } from '@/lib/utils'
import { balanceClass, profitClass } from './amountTone'
import { Money } from './Money'

const AMOUNT_COLUMNS = ['Saldo inicial', 'Ingresos', 'Egresos', 'Profit', 'Saldo final']

function AccountRow({ account }: { account: AccountBalance }) {
  return (
    <TableRow className={cn(account.isInRed && 'bg-red-500/[0.06] hover:bg-red-500/10')}>
      <TableCell className="font-medium">{account.accountName}</TableCell>
      <TableCell>
        <Badge variant="outline" className={cn('rounded-full', !account.isActive && 'text-muted-foreground')}>
          {account.isActive ? 'Activa' : 'Inactiva'}
        </Badge>
      </TableCell>
      <TableCell className="text-right">
        <Money value={account.openingBalance} className={balanceClass(account.openingBalance)} />
      </TableCell>
      <TableCell className="text-right"><Money value={account.totalIncome} /></TableCell>
      <TableCell className="text-right"><Money value={account.totalExpense} /></TableCell>
      <TableCell className="text-right">
        <Money value={account.profit} className={profitClass(account.profit)} />
      </TableCell>
      <TableCell className="text-right">
        <span className="inline-flex items-center gap-2">
          {account.isInRed && <Badge variant="destructive" className="rounded-full">En rojo</Badge>}
          <Money value={account.closingBalance} className={cn('font-semibold', balanceClass(account.closingBalance))} />
        </span>
      </TableCell>
    </TableRow>
  )
}

function AccountsGrid({ accounts }: { accounts: AccountBalance[] }) {
  return (
    <Table className="text-sm">
      <TableHeader>
        <TableRow>
          <TableHead>Cuenta</TableHead>
          <TableHead>Estado</TableHead>
          {AMOUNT_COLUMNS.map((title) => (
            <TableHead key={title} className="text-right">{title}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {accounts.map((account) => <AccountRow key={account.accountId} account={account} />)}
      </TableBody>
    </Table>
  )
}

// Below md the 7-column table would scroll sideways and hide "Saldo final", so each account becomes a row card.
function AccountsList({ accounts }: { accounts: AccountBalance[] }) {
  return (
    <ul className="divide-y divide-white/[0.06] md:hidden">
      {accounts.map((account) => (
        <li key={account.accountId} className="space-y-2 py-3">
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium">{account.accountName}</span>
            <span className="inline-flex items-center gap-2">
              {account.isInRed && <Badge variant="destructive" className="rounded-full">En rojo</Badge>}
              <Money value={account.closingBalance} className={cn('font-semibold', balanceClass(account.closingBalance))} />
            </span>
          </div>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <dt>Saldo inicial</dt><dd className="text-right"><Money value={account.openingBalance} /></dd>
            <dt>Ingresos</dt><dd className="text-right"><Money value={account.totalIncome} /></dd>
            <dt>Egresos</dt><dd className="text-right"><Money value={account.totalExpense} /></dd>
            <dt>Profit</dt><dd className="text-right"><Money value={account.profit} className={profitClass(account.profit)} /></dd>
          </dl>
        </li>
      ))}
    </ul>
  )
}

export function AccountsTable({ accounts, period }: { accounts: AccountBalance[]; period: string }) {
  return (
    <Card className="rounded-2xl border border-white/[0.06] py-5 ring-0">
      <CardHeader className="px-5">
        <CardTitle>Detalle por cuenta</CardTitle>
        <CardDescription>Importes en MXN · {period}</CardDescription>
      </CardHeader>
      <CardContent className="px-5">
        {accounts.length === 0 ? (
          <p className="rounded-xl border border-dashed border-white/10 p-8 text-center text-muted-foreground">
            La empresa no tiene cuentas registradas, por eso no hay detalle que mostrar.
          </p>
        ) : (
          <>
            <div className="hidden md:block"><AccountsGrid accounts={accounts} /></div>
            <AccountsList accounts={accounts} />
          </>
        )}
        <p className="mt-4 text-sm text-muted-foreground">
          <span className="text-red-400">Rojo</span> = saldo negativo (cuenta en rojo) ·{' '}
          <span className="text-warning">Ámbar</span> = profit negativo (pérdida en el período; el saldo puede
          seguir positivo)
        </p>
      </CardContent>
    </Card>
  )
}
