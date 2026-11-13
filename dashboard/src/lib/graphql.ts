const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8004/graphql'

export type ApiErrorCode = 'UNAUTHENTICATED' | 'FORBIDDEN' | 'BAD_USER_INPUT' | 'NETWORK' | 'UNKNOWN'

export class ApiError extends Error {
  readonly code: ApiErrorCode

  constructor(message: string, code: ApiErrorCode) {
    super(message)
    this.code = code
  }
}

interface GraphQLResponse<T> {
  data?: T | null
  errors?: { message: string }[]
}

// The backend raises AppError with a plain message and no `extensions.code` (services/auth.py,
// services/permission_service.py, services/balance_service.py), so the message is the only signal.
const RULES: readonly [ApiErrorCode, RegExp][] = [
  // leer_actor: missing/invalid/expired token or a membership that no longer applies -> back to login.
  ['UNAUTHENTICATED', /falta el token|token no es válido|ya venció|membresía no existe|token no corresponde|usuario está inactivo/i],
  // exigir_permiso: valid session without read permissions -> "Acceso denegado", no numbers.
  ['FORBIDDEN', /permiso denegado|no tiene un rol activo|está desactivado|token no pertenece/i],
  // fromDate > toDate, or a Date variable Strawberry could not parse.
  ['BAD_USER_INPUT', /fromDate no puede|has invalid value|inválid/i],
]

export function classifyError(message: string): ApiErrorCode {
  return RULES.find(([, pattern]) => pattern.test(message))?.[0] ?? 'UNKNOWN'
}

/** Minimal GraphQL client: POST + optional Bearer token, errors normalized to ApiError. */
export async function gql<T>(query: string, variables: Record<string, unknown> = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(API_URL, { method: 'POST', headers, body: JSON.stringify({ query, variables }) })
  } catch {
    throw new ApiError('No se pudo conectar con el servidor. Verifica que el API esté en ejecución.', 'NETWORK')
  }

  let body: GraphQLResponse<T>
  try {
    body = (await response.json()) as GraphQLResponse<T>
  } catch {
    throw new ApiError(`El servidor respondió con un formato inesperado (HTTP ${response.status}).`, 'UNKNOWN')
  }

  const first = body.errors?.[0]
  if (first) throw new ApiError(first.message, classifyError(first.message))
  if (!body.data) throw new ApiError('El servidor no devolvió datos.', 'UNKNOWN')
  return body.data
}
