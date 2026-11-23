import { ApiError, gql } from './graphql'

const ROLE_ORDER = ['ADMINISTRADOR', 'CONTADOR', 'CAPTURISTA', 'CONSULTA']

const PERMISSION_GROUPS = [
  ['Usuarios', 'company.users'],
  ['Cuentas', 'accounts'],
  ['Conceptos', 'concepts'],
  ['Movimientos', 'transactions'],
  ['Roles', 'roles'],
]

const CATALOG_FIELDS = 'id code name'
const ROLES = `roles(activeOnly: true) { ${CATALOG_FIELDS} }`
const MATRIX = `query Matriz {
  ${ROLES}
  permissions(activeOnly: true) { ${CATALOG_FIELDS} }
}`
const ROLE_PERMISSIONS = `query ListaDelRol($roleId: ID!) {
  rolePermissions(roleId: $roleId) { isActive permission { id code } }
}`
const PREVIEW = `query VistaPrevia($input: SetRolePermissionsInput!) {
  previewRolePermissions(input: $input) {
    toActivate { code } toDeactivate { code } unchanged { code } finalCount
  }
}`
const SAVE = `mutation GuardarColumna($input: SetRolePermissionsInput!) {
  setRolePermissions(input: $input) { activated { code } deactivated { code } finalCount changed }
}`
const ASSIGN = `mutation AsignarPuesto($input: AssignRoleInput!) {
  assignRole(input: $input) { isActive role { code name } }
}`

export interface CatalogEntry { id: string; code: string; name: string }
export interface RoleColumn { role: CatalogEntry; permissionIds: string[] }
interface RoleInput { roleId: string; permissionIds: string[] }
interface PermissionCode { code: string }
export interface RolePreview {
  toActivate: PermissionCode[]; toDeactivate: PermissionCode[]; unchanged: PermissionCode[]; finalCount: number
}
export interface RoleUpdate {
  activated: PermissionCode[]; deactivated: PermissionCode[]; finalCount: number; changed: boolean
}

function orderedRoles(roles: CatalogEntry[]) {
  return ROLE_ORDER.flatMap((code) => roles.filter((role) => role.code === code))
}

export async function fetchRoles(token: string) {
  const { roles } = await gql<{ roles: CatalogEntry[] }>(`query RolesActivos { ${ROLES} }`, {}, token)
  return orderedRoles(roles)
}

export async function fetchRoleColumn(token: string, role: CatalogEntry, activeIds: Set<string>): Promise<RoleColumn> {
  const { rolePermissions } = await gql<{
    rolePermissions: { isActive: boolean; permission: { id: string; code: string } }[]
  }>(ROLE_PERMISSIONS, { roleId: role.id }, token)
  return {
    role,
    permissionIds: rolePermissions.filter(({ isActive, permission }) => isActive && activeIds.has(permission.id))
      .map(({ permission }) => permission.id),
  }
}

export async function fetchRoleMatrix(token: string) {
  const { roles, permissions } = await gql<{ roles: CatalogEntry[]; permissions: CatalogEntry[] }>(MATRIX, {}, token)
  const activeIds = new Set(permissions.map(({ id }) => id))
  const groups = PERMISSION_GROUPS.map(([name, prefix]) => ({
    name,
    permissions: ['read', 'write'].flatMap((action) => permissions.filter(({ code }) => code === `${prefix}.${action}`)),
  })).filter((group) => group.permissions.length > 0)
  const columns = groups.length
    ? await Promise.all(orderedRoles(roles).map((role) => fetchRoleColumn(token, role, activeIds)))
    : []
  return { columns, groups, activeIds }
}

export async function previewRolePermissions(token: string, input: RoleInput) {
  const { previewRolePermissions: result } = await gql<{ previewRolePermissions: RolePreview | null }>(PREVIEW, { input }, token)
  if (!result) throw new ApiError('El API no devolvió la vista previa.', 'UNKNOWN')
  return result
}

export async function setRolePermissions(token: string, input: RoleInput) {
  const { setRolePermissions: result } = await gql<{ setRolePermissions: RoleUpdate | null }>(SAVE, { input }, token)
  if (!result) throw new ApiError('El API no confirmó el guardado.', 'UNKNOWN')
  return result
}

export async function assignRole(token: string, companyUserId: string, roleId: string) {
  const { assignRole: result } = await gql<{
    assignRole: { isActive: boolean; role: Pick<CatalogEntry, 'code' | 'name'> }
  }>(ASSIGN, { input: { companyUserId, roleId } }, token)
  if (!result.isActive) throw new ApiError('El API no confirmó un rol activo.', 'UNKNOWN')
  return result.role
}
