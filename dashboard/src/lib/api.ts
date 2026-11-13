import { ApiError, gql } from './graphql'
import type { Period } from './period'
import type { Session, SessionUser } from './session'

/** Decimal scalar: the backend serializes it as a string such as "1600.00". Never convert to number. */
export type Decimal = string

export interface AccountBalance {
  accountId: string
  accountName: string
  isActive: boolean
  openingBalance: Decimal
  totalIncome: Decimal
  totalExpense: Decimal
  profit: Decimal
  closingBalance: Decimal
  isInRed: boolean
}

export interface GeneralBalance {
  companyId: string
  currency: string
  fromDate: string
  toDate: string
  openingBalance: Decimal
  totalIncome: Decimal
  totalExpense: Decimal
  profit: Decimal
  closingBalance: Decimal
  isInRed: boolean
  accountsInRed: number
  accounts: AccountBalance[]
}

const LOGIN = `mutation IniciarSesion($email: String!, $password: String!) {
  login(input: { email: $email, password: $password }) { token tokenType user { id name email } }
}`

const COMPANY = `query EmpresaDelToken($id: ID!) { company(id: $id) { name } }`

const BALANCE_FIELDS = 'openingBalance totalIncome totalExpense profit closingBalance isInRed'

const GENERAL_BALANCE = `query IndicadoresEmpresa($from: Date!, $to: Date!) {
  generalBalance(fromDate: $from, toDate: $to) {
    companyId currency fromDate toDate ${BALANCE_FIELDS} accountsInRed
    accounts { accountId accountName isActive ${BALANCE_FIELDS} }
  }
}`

export async function login(email: string, password: string): Promise<Session> {
  const data = await gql<{ login: { token: string; user: SessionUser } }>(LOGIN, { email, password })
  return { token: data.login.token, user: data.login.user }
}

/**
 * Reads `companyId` from the JWT payload (signed by the backend in services/auth.py). It is only used to
 * show the company name; the signature is verified by the backend on every balance request.
 */
export function companyIdFromToken(token: string): string {
  try {
    const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload: unknown = JSON.parse(atob(part.padEnd(Math.ceil(part.length / 4) * 4, '=')))
    const id = (payload as { companyId?: unknown }).companyId
    if (typeof id === 'number' || typeof id === 'string') return String(id)
  } catch {
    // Falls through to the error below: a token we cannot read is as good as an invalid one.
  }
  throw new ApiError('El token no es válido o ya venció', 'UNAUTHENTICATED')
}

/** The schema has no `me` query: the public `company(id)` query resolves the name of the token's company. */
export async function fetchCompanyName(token: string): Promise<string> {
  const id = companyIdFromToken(token)
  const data = await gql<{ company: { name: string } | null }>(COMPANY, { id })
  return data.company?.name ?? `Empresa ${id}`
}

export async function fetchGeneralBalance(token: string, period: Period): Promise<GeneralBalance> {
  const variables = { from: period.fromDate, to: period.toDate }
  const data = await gql<{ generalBalance: GeneralBalance }>(GENERAL_BALANCE, variables, token)
  return data.generalBalance
}
