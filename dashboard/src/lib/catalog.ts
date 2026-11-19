import type { Account, AccountType, CompanyUser, ConceptType } from './admin'

/** Catálogo de tipos del Parcial I con su etiqueta en pantalla (no se muestra el código crudo). */
export const ACCOUNT_TYPES: readonly { value: AccountType; label: string }[] = [
  { value: 'CASH', label: 'Efectivo' },
  { value: 'DEBIT', label: 'Débito' },
  { value: 'CREDIT', label: 'Crédito' },
  { value: 'SAVINGS', label: 'Ahorro' },
  { value: 'INVESTMENT', label: 'Inversión' },
  { value: 'WALLET', label: 'Monedero' },
  { value: 'OTHER', label: 'Otro' },
]

export function accountTypeLabel(type: AccountType): string {
  return ACCOUNT_TYPES.find((t) => t.value === type)?.label ?? type
}

export const CONCEPT_TYPE_LABELS: Record<ConceptType, string> = { INCOME: 'Ingreso', EXPENSE: 'Egreso' }

/** Referencia enmascarada: CLABE (****1234) o últimos dígitos de tarjeta. Nunca los 18 dígitos. */
export function accountReference(account: Pick<Account, 'maskedClabe' | 'cardLastDigits'>): string | null {
  if (account.maskedClabe) return account.maskedClabe
  if (account.cardLastDigits) return `****${account.cardLastDigits}`
  return null
}

export interface UserCounts {
  active: number
  admins: number
  inactive: number
}

/** Los tres conteos de la pantalla Usuarios, con la misma lista de companyUsers (sin otra consulta). */
export function countUsers(users: readonly CompanyUser[]): UserCounts {
  return {
    active: users.filter((u) => u.isActive).length,
    // Debe ser 0 o 1; si llega más de uno es un error de datos del Parcial I y se muestra, no se oculta.
    admins: users.filter((u) => u.isAdmin).length,
    inactive: users.filter((u) => !u.isActive).length,
  }
}

export type StatusFilter = 'all' | 'active' | 'inactive'

export function matchesStatus(isActive: boolean, filter: StatusFilter): boolean {
  return filter === 'all' || (filter === 'active') === isActive
}

function normalize(text: string): string {
  return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()
}

/** Búsqueda en pantalla por nombre o correo, sin acentos ni mayúsculas. */
export function filterUsers(users: readonly CompanyUser[], search: string, status: StatusFilter): CompanyUser[] {
  const term = normalize(search)
  return users.filter((u) => matchesStatus(u.isActive, status)
    && (!term || normalize(u.user.name).includes(term) || normalize(u.user.email).includes(term)))
}

export function can(permissions: readonly string[], code: string): boolean {
  return permissions.includes(code)
}

const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

/** Fecha de ingreso en la zona horaria de quien mira: un alta a las 20:00 de México es de hoy, no de mañana (UTC). */
export function formatJoinedAt(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return `${date.getDate()} ${MONTHS[date.getMonth()]} ${date.getFullYear()}`
}
