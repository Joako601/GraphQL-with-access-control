import { useCallback, useState, type FormEvent } from 'react'
import { Loader2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useApiQuery, useMutation } from '@/hooks/useApiQuery'
import { createAccount, fetchAccounts, type Account, type AccountType, type NewAccount } from '@/lib/admin'
import { ACCOUNT_TYPES, accountReference, accountTypeLabel, can } from '@/lib/catalog'
import { cn } from '@/lib/utils'
import type { AdminContext } from './AdminPage'
import {
  CARD, Denied, EmptyState, Field, FIELD, FormError, FormPanel, LoadFailed, ModuleTitle, NativeSelect, PRIMARY,
  SegmentedFilter, SourceNote, StatusBadge, TableSkeleton, TextArea,
} from './parts'

type TypeFilter = 'ALL' | AccountType
const TYPE_OPTIONS: readonly { value: TypeFilter; label: string }[] = [{ value: 'ALL', label: 'Todas' }, ...ACCOUNT_TYPES]
const ACTIVE_OPTIONS = [{ value: 'all', label: 'Todas' }, { value: 'active', label: 'Solo activas' }] as const

function AccountsTable({ accounts }: { accounts: Account[] }) {
  return (
    <Table className="text-sm">
      <TableHeader>
        <TableRow>
          <TableHead>Nombre</TableHead>
          <TableHead>Tipo</TableHead>
          <TableHead>Banco</TableHead>
          <TableHead>Referencia</TableHead>
          <TableHead>Estado</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {accounts.map((a) => (
          <TableRow key={a.id} className={cn(!a.isActive && 'text-muted-foreground')}>
            <TableCell>
              <p className="font-medium">{a.name}</p>
              {a.shortDescription && <p className="text-xs text-muted-foreground">{a.shortDescription}</p>}
            </TableCell>
            <TableCell>{accountTypeLabel(a.accountType)}</TableCell>
            {/* Vacío si la cuenta no es bancaria (Caja). */}
            <TableCell>{a.bankName ?? <span className="text-muted-foreground">—</span>}</TableCell>
            <TableCell className="font-mono tabular-nums">
              {accountReference(a) ?? <span className="font-sans text-muted-foreground">—</span>}
            </TableCell>
            <TableCell><StatusBadge active={a.isActive} feminine /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

// Debajo de md cada cuenta es una tarjeta, sin desplazamiento lateral.
function AccountsCards({ accounts }: { accounts: Account[] }) {
  return (
    <ul className="divide-y divide-white/[0.06]">
      {accounts.map((a) => (
        <li key={a.id} className={cn('space-y-1 py-3', !a.isActive && 'text-muted-foreground')}>
          <div className="flex items-start justify-between gap-2">
            <p className="font-medium">{a.name}</p>
            <StatusBadge active={a.isActive} feminine />
          </div>
          <p className="text-xs text-muted-foreground">
            {accountTypeLabel(a.accountType)} · {a.bankName ?? 'Sin banco'} · {accountReference(a) ?? 'Sin referencia'}
          </p>
          {a.shortDescription && <p className="text-xs text-muted-foreground">{a.shortDescription}</p>}
        </li>
      ))}
    </ul>
  )
}

const EMPTY_FORM: NewAccount = { name: '', accountType: 'DEBIT', bankName: '', clabe: '', shortDescription: '' }

function NewAccountForm({ ctx, onCreated, onClose }: { ctx: AdminContext; onCreated: () => void; onClose: () => void }) {
  const [form, setForm] = useState<NewAccount>(EMPTY_FORM)
  const { run, pending, error } = useMutation(ctx.onUnauthenticated)
  const isCash = form.accountType === 'CASH'

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (await run(() => createAccount(ctx.token, ctx.companyId, { ...form, name: form.name.trim() }))) {
      toast.success(`Cuenta «${form.name.trim()}» creada`)
      setForm(EMPTY_FORM)
      onCreated()
    }
  }

  return (
    <FormPanel title="Nueva cuenta" onClose={onClose}
      note="Banco y CLABE pueden ir vacíos en una cuenta de efectivo. El servidor valida que la cuenta sea de tu empresa.">
      <form onSubmit={(e) => void submit(e)} className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Field id="na-name" label="Nombre">
            <Input id="na-name" required value={form.name} className={FIELD}
              onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field id="na-type" label="Tipo de cuenta">
            <NativeSelect id="na-type" value={form.accountType}
              onChange={(e) => setForm({ ...form, accountType: e.target.value as AccountType })}>
              {ACCOUNT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </NativeSelect>
          </Field>
          <Field id="na-bank" label="Banco" hint={isCash ? 'Efectivo: puede ir sin banco.' : 'Opcional.'}>
            <Input id="na-bank" value={form.bankName} className={FIELD}
              onChange={(e) => setForm({ ...form, bankName: e.target.value })} />
          </Field>
          <Field id="na-clabe" label="CLABE" hint="18 dígitos, opcional. La tabla solo muestra los últimos 4.">
            <Input id="na-clabe" inputMode="numeric" maxLength={18} autoComplete="off" value={form.clabe}
              className={cn(FIELD, 'font-mono')}
              onChange={(e) => setForm({ ...form, clabe: e.target.value.replace(/\s/g, '') })} />
          </Field>
        </div>
        <Field id="na-desc" label="Descripción corta">
          <TextArea id="na-desc" maxLength={255} value={form.shortDescription} className="min-h-16"
            onChange={(e) => setForm({ ...form, shortDescription: e.target.value })} />
        </Field>
        <FormError message={error} />
        <Button type="submit" disabled={pending} className={PRIMARY}>
          {pending && <Loader2 className="animate-spin" />}
          Guardar
        </Button>
      </form>
    </FormPanel>
  )
}

export function AccountsModule({ ctx }: { ctx: AdminContext }) {
  const fetcher = useCallback(() => fetchAccounts(ctx.token, ctx.companyId), [ctx.token, ctx.companyId])
  const { state, reload } = useApiQuery(fetcher, ctx.onUnauthenticated)
  const [type, setType] = useState<TypeFilter>('ALL')
  const [active, setActive] = useState<'all' | 'active'>('all')
  const [formOpen, setFormOpen] = useState(false)
  const canWrite = can(ctx.permissions, 'accounts.write')

  const action = canWrite && !formOpen ? (
    <Button className={PRIMARY} onClick={() => setFormOpen(true)}><Plus />Nueva cuenta</Button>
  ) : null

  if (state.status === 'error') {
    return (
      <section className="space-y-5">
        <ModuleTitle title="Cuentas" question="¿Dónde está el dinero?" />
        {state.error.code === 'FORBIDDEN' ? <Denied error={state.error} /> : <LoadFailed error={state.error} onRetry={reload} />}
      </section>
    )
  }

  return (
    <section className="space-y-5">
      <ModuleTitle title="Cuentas" question="¿Dónde está el dinero?" action={action} />
      {formOpen && canWrite && <NewAccountForm ctx={ctx} onCreated={reload} onClose={() => setFormOpen(false)} />}
      <Card className={CARD}>
        <CardContent className="space-y-4 px-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <SegmentedFilter label="Tipo de cuenta" options={TYPE_OPTIONS} value={type} onChange={setType} />
            <SegmentedFilter label="Estado" options={ACTIVE_OPTIONS} value={active} onChange={setActive} />
          </div>
          {state.status === 'loading' && <TableSkeleton label="Cargando cuentas" />}
          {state.status === 'success' && (() => {
            const rows = state.data.filter((a) => (type === 'ALL' || a.accountType === type)
              && (active === 'all' || a.isActive))
            if (state.data.length === 0) return <EmptyState>La empresa no tiene cuentas registradas.</EmptyState>
            if (rows.length === 0) return <EmptyState>No hay cuentas con ese filtro.</EmptyState>
            return (
              <>
                <div className="hidden md:block"><AccountsTable accounts={rows} /></div>
                <div className="md:hidden"><AccountsCards accounts={rows} /></div>
              </>
            )
          })()}
          <SourceNote>
            Los datos salen de <code>accounts</code>. La CLABE llega enmascarada (<code>maskedClabe</code>).
          </SourceNote>
        </CardContent>
      </Card>
    </section>
  )
}
