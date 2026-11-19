import { gql } from './graphql'

// Unidad III, Actividad 2: lecturas y altas del dashboard administrativo. Cada tabla es una query y cada
// botón Guardar una mutation; el token viaja en Authorization: Bearer y la empresa sale de `me`.

export type AccountType = 'CASH' | 'DEBIT' | 'CREDIT' | 'SAVINGS' | 'INVESTMENT' | 'WALLET' | 'OTHER'
export type ConceptType = 'INCOME' | 'EXPENSE'

/** `me`: membership of the session token, with its role and permission codes (e.g. "accounts.write"). */
export interface Me {
  companyUserId: string
  companyId: string
  isAdmin: boolean
  user: { name: string; email: string }
  company: { name: string }
  role: { code: string; name: string } | null
  permissions: string[]
}

export interface CompanyUser {
  id: string
  isAdmin: boolean
  isActive: boolean
  joinedAt: string
  user: { name: string; email: string }
  role: { code: string; name: string } | null
}

export interface Account {
  id: string
  name: string
  accountType: AccountType
  bankName: string | null
  maskedClabe: string | null
  cardLastDigits: string | null
  shortDescription: string | null
  isActive: boolean
}

export interface Concept {
  id: string
  name: string
  conceptType: ConceptType
  shortDescription: string | null
  isActive: boolean
}

export interface AccountConcept {
  id: string
  isActive: boolean
  concept: { id: string; name: string; conceptType: ConceptType }
}

const ME = `query SesionActual {
  me {
    companyUserId companyId isAdmin
    user { name email }
    company { name }
    role { code name }
    permissions
  }
}`

// La contraseña no se pide en ninguna lectura: el tipo User del API ni siquiera la expone.
const COMPANY_USERS = `query Usuarios($companyId: ID!) {
  companyUsers(companyId: $companyId) {
    id isAdmin isActive joinedAt
    user { name email }
    role { code name }
  }
}`

// maskedClabe (****1234) en lugar de clabe: la tabla no recibe los 18 dígitos.
const ACCOUNTS = `query Cuentas($companyId: ID!) {
  accounts(companyId: $companyId) {
    id name accountType bankName maskedClabe cardLastDigits shortDescription isActive
  }
}`

const CONCEPTS = `query Conceptos($companyId: ID!) {
  concepts(companyId: $companyId) { id name conceptType shortDescription isActive }
}`

const ACCOUNT_CONCEPTS = `query ConceptosDeCuenta($accountId: ID!) {
  accountConcepts(accountId: $accountId, activeOnly: true) {
    id isActive
    concept { id name conceptType }
  }
}`

const CREATE_COMPANY_USER = `mutation NuevoUsuario($input: CreateCompanyUserInput!) {
  createCompanyUser(input: $input) { id isActive user { name email } }
}`

const DEACTIVATE_COMPANY_USER = `mutation DesactivarUsuario($id: ID!) {
  deactivateCompanyUser(id: $id) { id isActive }
}`

const CREATE_ACCOUNT = `mutation NuevaCuenta($input: CreateAccountInput!) {
  createAccount(input: $input) { id name accountType isActive }
}`

const CREATE_CONCEPT = `mutation NuevoConcepto($input: CreateConceptInput!) {
  createConcept(input: $input) { id name conceptType isActive }
}`

const ASSIGN_CONCEPT = `mutation AsignarConcepto($input: AssignConceptToAccountInput!) {
  assignConceptToAccount(input: $input) { id isActive }
}`

const REMOVE_CONCEPT = `mutation QuitarConcepto($accountId: ID!, $conceptId: ID!) {
  removeConceptFromAccount(accountId: $accountId, conceptId: $conceptId)
}`

export async function fetchMe(token: string): Promise<Me> {
  return (await gql<{ me: Me }>(ME, {}, token)).me
}

export async function fetchCompanyUsers(token: string, companyId: string): Promise<CompanyUser[]> {
  return (await gql<{ companyUsers: CompanyUser[] }>(COMPANY_USERS, { companyId }, token)).companyUsers
}

export async function fetchAccounts(token: string, companyId: string): Promise<Account[]> {
  return (await gql<{ accounts: Account[] }>(ACCOUNTS, { companyId }, token)).accounts
}

export async function fetchConcepts(token: string, companyId: string): Promise<Concept[]> {
  return (await gql<{ concepts: Concept[] }>(CONCEPTS, { companyId }, token)).concepts
}

export async function fetchAccountConcepts(token: string, accountId: string): Promise<AccountConcept[]> {
  return (await gql<{ accountConcepts: AccountConcept[] }>(ACCOUNT_CONCEPTS, { accountId }, token)).accountConcepts
}

export interface NewCompanyUser {
  name: string
  email: string
  password: string
}

/** No isAdmin: the principal administrator already exists (createCompanyAdmin, Parcial I). */
export async function createCompanyUser(token: string, companyId: string, input: NewCompanyUser): Promise<void> {
  await gql(CREATE_COMPANY_USER, { input: { companyId, ...input } }, token)
}

export async function deactivateCompanyUser(token: string, id: string): Promise<void> {
  await gql(DEACTIVATE_COMPANY_USER, { id }, token)
}

export interface NewAccount {
  name: string
  accountType: AccountType
  bankName: string
  clabe: string
  shortDescription: string
}

/** Empty optional fields travel as null: a cash account has no bank or CLABE. */
export async function createAccount(token: string, companyId: string, input: NewAccount): Promise<void> {
  const optional = (value: string) => value.trim() || null
  await gql(CREATE_ACCOUNT, {
    input: {
      companyId,
      name: input.name,
      accountType: input.accountType,
      bankName: optional(input.bankName),
      clabe: optional(input.clabe),
      shortDescription: optional(input.shortDescription),
    },
  }, token)
}

export interface NewConcept {
  name: string
  conceptType: ConceptType
  shortDescription: string
}

export async function createConcept(token: string, companyId: string, input: NewConcept): Promise<void> {
  await gql(CREATE_CONCEPT, {
    input: { companyId, ...input, shortDescription: input.shortDescription.trim() || null },
  }, token)
}

export async function assignConceptToAccount(token: string, accountId: string, conceptId: string): Promise<void> {
  await gql(ASSIGN_CONCEPT, { input: { accountId, conceptId } }, token)
}

export async function removeConceptFromAccount(token: string, accountId: string, conceptId: string): Promise<void> {
  await gql(REMOVE_CONCEPT, { accountId, conceptId }, token)
}
