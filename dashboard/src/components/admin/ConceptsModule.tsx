import { useCallback, useState, type FormEvent } from 'react'
import { CircleCheck, Loader2, Plus, X } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useApiQuery, useMutation, type QueryState } from '@/hooks/useApiQuery'
import {
  assignConceptToAccount, createConcept, fetchAccountConcepts, fetchAccounts, fetchConcepts, removeConceptFromAccount,
  type Account, type Concept, type ConceptType, type NewConcept,
} from '@/lib/admin'
import { can, CONCEPT_TYPE_LABELS } from '@/lib/catalog'
import { cn } from '@/lib/utils'
import type { AdminContext } from './AdminPage'
import {
  CARD, Denied, EmptyState, Field, FIELD, FormError, LoadFailed, ModuleTitle, NativeSelect, PRIMARY, SegmentedFilter,
  SourceNote, StatusBadge, TableSkeleton, TextArea,
} from './parts'

type TypeFilter = 'ALL' | ConceptType
const TYPE_OPTIONS = [
  { value: 'ALL', label: 'Todos' }, { value: 'INCOME', label: 'Ingreso' }, { value: 'EXPENSE', label: 'Egreso' },
] as const
const ACTIVE_OPTIONS = [{ value: 'all', label: 'Todos' }, { value: 'active', label: 'Solo activos' }] as const

const EMPTY_FORM: NewConcept = { name: '', conceptType: 'INCOME', shortDescription: '' }

function NewConceptForm({ ctx, onCreated, onClose }: { ctx: AdminContext; onCreated: () => void; onClose: () => void }) {
  const [form, setForm] = useState<NewConcept>(EMPTY_FORM)
  const { run, pending, error } = useMutation(ctx.onUnauthenticated)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (await run(() => createConcept(ctx.token, ctx.companyId, { ...form, name: form.name.trim() }))) {
      toast.success(`Concepto «${form.name.trim()}» creado`)
      setForm(EMPTY_FORM)
      onCreated()
    }
  }

  return (
    <form onSubmit={(e) => void submit(e)} className="space-y-4 rounded-xl border border-white/10 p-4">
      <div className="flex items-center justify-between">
        <p className="font-medium">Nuevo concepto</p>
        <Button type="button" variant="ghost" size="icon-sm" aria-label="Cerrar formulario" onClick={onClose}><X /></Button>
      </div>
      <Field id="nc-name" label="Nombre">
        <Input id="nc-name" required value={form.name} className={FIELD}
          onChange={(e) => setForm({ ...form, name: e.target.value })} />
      </Field>
      {/* El tipo es uno: no existe un concepto "de las dos cosas". */}
      <fieldset className="space-y-1.5">
        <legend className="text-sm font-medium">Tipo</legend>
        <div className="flex gap-4 pt-1">
          {(['INCOME', 'EXPENSE'] as const).map((t) => (
            <label key={t} className="flex items-center gap-2 text-sm">
              <input type="radio" name="nc-type" value={t} checked={form.conceptType === t}
                onChange={() => setForm({ ...form, conceptType: t })} className="accent-white" />
              {CONCEPT_TYPE_LABELS[t]}
            </label>
          ))}
        </div>
      </fieldset>
      <Field id="nc-desc" label="Descripción corta">
        <TextArea id="nc-desc" maxLength={255} value={form.shortDescription}
          onChange={(e) => setForm({ ...form, shortDescription: e.target.value })} />
      </Field>
      <FormError message={error} />
      <Button type="submit" disabled={pending} className={cn(PRIMARY, 'w-full')}>
        {pending && <Loader2 className="animate-spin" />}
        Guardar
      </Button>
    </form>
  )
}

function Catalog({ ctx, state, reload, canWrite }: {
  ctx: AdminContext; state: QueryState<Concept[]>; reload: () => void; canWrite: boolean
}) {
  const [type, setType] = useState<TypeFilter>('ALL')
  const [active, setActive] = useState<'all' | 'active'>('all')
  const [formOpen, setFormOpen] = useState(false)

  return (
    <Card className={cn(CARD, 'min-w-0')}>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 px-5">
        <div>
          <CardTitle>Catálogo</CardTitle>
          <CardDescription>Qué conceptos existen en la empresa.</CardDescription>
        </div>
        {canWrite && !formOpen && (
          <Button className={PRIMARY} onClick={() => setFormOpen(true)}><Plus />Nuevo concepto</Button>
        )}
      </CardHeader>
      <CardContent className="space-y-4 px-5">
        {formOpen && canWrite && <NewConceptForm ctx={ctx} onCreated={reload} onClose={() => setFormOpen(false)} />}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <SegmentedFilter label="Tipo de concepto" options={TYPE_OPTIONS} value={type} onChange={setType} />
          <SegmentedFilter label="Estado" options={ACTIVE_OPTIONS} value={active} onChange={setActive} />
        </div>
        {state.status === 'loading' && <TableSkeleton label="Cargando conceptos" />}
        {state.status === 'error' && state.error.code === 'FORBIDDEN' && <Denied error={state.error} />}
        {state.status === 'error' && state.error.code !== 'FORBIDDEN' && <LoadFailed error={state.error} onRetry={reload} />}
        {state.status === 'success' && (() => {
          const rows = state.data.filter((c) => (type === 'ALL' || c.conceptType === type) && (active === 'all' || c.isActive))
          if (state.data.length === 0) return <EmptyState>La empresa no tiene conceptos en el catálogo.</EmptyState>
          if (rows.length === 0) return <EmptyState>No hay conceptos con ese filtro.</EmptyState>
          return (
            <div className="overflow-x-auto">
              <Table className="text-sm">
                <TableHeader>
                  <TableRow>
                    <TableHead>Concepto</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Estado</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((c) => (
                    <TableRow key={c.id} className={cn(!c.isActive && 'text-muted-foreground')}>
                      <TableCell>
                        <p className="font-medium">{c.name}</p>
                        {c.shortDescription && <p className="text-xs text-muted-foreground">{c.shortDescription}</p>}
                      </TableCell>
                      <TableCell>
                        <span className={c.conceptType === 'INCOME' ? 'text-emerald-300' : 'text-amber-300'}>
                          {CONCEPT_TYPE_LABELS[c.conceptType]}
                        </span>
                      </TableCell>
                      <TableCell><StatusBadge active={c.isActive} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )
        })()}
        <SourceNote>Los datos salen de <code>concepts</code>.</SourceNote>
      </CardContent>
    </Card>
  )
}

/** Lista y asignación de una sola cuenta. Se monta de nuevo (key) al elegir otra cuenta. */
function AccountConceptsEditor({ ctx, account, catalog, canWrite }: {
  ctx: AdminContext; account: Account; catalog: Concept[]; canWrite: boolean
}) {
  const [conceptId, setConceptId] = useState('')
  const fetcher = useCallback(() => fetchAccountConcepts(ctx.token, account.id), [ctx.token, account.id])
  const { state, reload } = useApiQuery(fetcher, ctx.onUnauthenticated)
  const assign = useMutation(ctx.onUnauthenticated)
  const remove = useMutation(ctx.onUnauthenticated)

  const assigned = state.status === 'success' ? state.data : []
  const assignedIds = new Set(assigned.map((ac) => ac.concept.id))
  // Se listan TODOS los conceptos activos, incluso los ya asignados: si se elige uno repetido, el API lo
  // rechaza y la pantalla muestra ese error (la regla vive en el servidor, no se esconde en el navegador).
  const options = catalog.filter((c) => c.isActive)

  async function handleAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!conceptId) return
    remove.clearError()
    if (await assign.run(() => assignConceptToAccount(ctx.token, account.id, conceptId))) {
      toast.success(`Concepto asignado a ${account.name}`)
      setConceptId('')
      reload()
    }
  }

  async function handleRemove(id: string, name: string) {
    assign.clearError() // el error anterior de "ya asignado" ya no aplica
    if (await remove.run(() => removeConceptFromAccount(ctx.token, account.id, id))) {
      toast.success(`«${name}» ya no se acepta en ${account.name}`, {
        description: 'El concepto sigue en el catálogo y los movimientos anteriores no cambian.',
      })
      reload()
    }
  }

  return (
    <>
      {state.status === 'loading' && <TableSkeleton label="Cargando conceptos de la cuenta" />}
      {state.status === 'error' && state.error.code === 'FORBIDDEN' && <Denied error={state.error} />}
      {state.status === 'error' && state.error.code !== 'FORBIDDEN' && (
        <LoadFailed error={state.error} onRetry={() => reload()} />
      )}
      {state.status === 'success' && (assigned.length === 0 ? (
        <EmptyState>La cuenta {account.name} todavía no tiene conceptos asignados.</EmptyState>
      ) : (
        <ul className="divide-y divide-white/[0.06] rounded-xl border border-white/10">
          {assigned.map((ac) => (
            <li key={ac.id} className="flex items-center justify-between gap-3 px-4 py-2.5">
              <span className="flex items-center gap-2">
                <CircleCheck className="size-4 text-emerald-400" />
                <span className="font-medium">{ac.concept.name}</span>
                <span className="text-xs text-muted-foreground">{CONCEPT_TYPE_LABELS[ac.concept.conceptType]}</span>
              </span>
              {canWrite && (
                <Button size="sm" variant="ghost" className="rounded-full text-red-300 hover:text-red-200"
                  disabled={remove.pending} onClick={() => void handleRemove(ac.concept.id, ac.concept.name)}>
                  Quitar
                </Button>
              )}
            </li>
          ))}
        </ul>
      ))}
      <FormError message={remove.error} />

      {canWrite && (
        <form onSubmit={(e) => void handleAssign(e)} className="space-y-3 border-t border-white/[0.06] pt-4">
          <Field id="ac-concept" label="Concepto a asignar">
            <NativeSelect id="ac-concept" value={conceptId} required onChange={(e) => setConceptId(e.target.value)}>
              <option value="">Elige un concepto…</option>
              {options.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} · {CONCEPT_TYPE_LABELS[c.conceptType]}{assignedIds.has(c.id) ? ' (ya asignado)' : ''}
                </option>
              ))}
            </NativeSelect>
          </Field>
          <FormError message={assign.error} />
          <Button type="submit" disabled={assign.pending} className={PRIMARY}>
            {assign.pending && <Loader2 className="animate-spin" />}
            Asignar concepto
          </Button>
        </form>
      )}
    </>
  )
}

function AccountPanel({ ctx, accounts, catalog, canWrite }: {
  ctx: AdminContext; accounts: Account[]; catalog: Concept[]; canWrite: boolean
}) {
  const [accountId, setAccountId] = useState(accounts[0].id)
  const account = accounts.find((a) => a.id === accountId) ?? accounts[0]

  return (
    <Card className={cn(CARD, 'min-w-0')}>
      <CardHeader className="px-5">
        <CardTitle>Conceptos de la cuenta {account.name}</CardTitle>
        <CardDescription>Qué conceptos acepta la cuenta elegida.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 px-5">
        <Field id="ac-account" label="Cuenta">
          <NativeSelect id="ac-account" value={account.id} onChange={(e) => setAccountId(e.target.value)}>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>{a.name}{a.isActive ? '' : ' (inactiva)'}</option>
            ))}
          </NativeSelect>
        </Field>
        <AccountConceptsEditor key={account.id} ctx={ctx} account={account} catalog={catalog} canWrite={canWrite} />
        <SourceNote>
          Solo los conceptos asignados se pueden usar en un movimiento. Los datos salen de <code>accountConcepts</code>.
        </SourceNote>
      </CardContent>
    </Card>
  )
}

export function ConceptsModule({ ctx }: { ctx: AdminContext }) {
  const conceptsFetcher = useCallback(() => fetchConcepts(ctx.token, ctx.companyId), [ctx.token, ctx.companyId])
  const accountsFetcher = useCallback(() => fetchAccounts(ctx.token, ctx.companyId), [ctx.token, ctx.companyId])
  const concepts = useApiQuery(conceptsFetcher, ctx.onUnauthenticated)
  const accounts = useApiQuery(accountsFetcher, ctx.onUnauthenticated)
  const canWrite = can(ctx.permissions, 'concepts.write')
  const catalog = concepts.state.status === 'success' ? concepts.state.data : []

  return (
    <section className="space-y-5">
      <ModuleTitle title="Conceptos" question="¿Por qué se mueve el dinero y en qué cuenta se permite?" />
      <div className="grid gap-5 xl:grid-cols-2">
        <Catalog ctx={ctx} state={concepts.state} reload={() => concepts.reload()} canWrite={canWrite} />
        {accounts.state.status === 'loading' && <TableSkeleton label="Cargando cuentas" />}
        {accounts.state.status === 'error' && (accounts.state.error.code === 'FORBIDDEN'
          ? <Denied error={accounts.state.error} />
          : <LoadFailed error={accounts.state.error} onRetry={() => accounts.reload()} />)}
        {accounts.state.status === 'success' && (accounts.state.data.length === 0 ? (
          <Card className={CARD}>
            <CardContent className="px-5">
              <EmptyState>No hay cuentas: crea una en el módulo Cuentas para asignarle conceptos.</EmptyState>
            </CardContent>
          </Card>
        ) : (
          <AccountPanel ctx={ctx} accounts={accounts.state.data} catalog={catalog} canWrite={canWrite} />
        ))}
      </div>
    </section>
  )
}
