import { describe, expect, it } from 'vitest'
import { classifyError } from './graphql'

// Messages copied verbatim from the backend (services/auth.py, permission_service.py, balance_service.py).
describe('classifyError', () => {
  it.each([
    'Falta el token: envía Authorization: Bearer <token>',
    'El token no es válido o ya venció',
    'La membresía no existe o no está activa',
    'El token no corresponde a esa empresa',
    'El usuario está inactivo',
  ])('treats "%s" as UNAUTHENTICATED (back to login)', (message) => {
    expect(classifyError(message)).toBe('UNAUTHENTICATED')
  })

  it.each([
    'Permiso denegado: el rol DEMO_SIN_LECTURA no tiene el permiso accounts.read',
    'La membresía no tiene un rol activo',
    'El rol CONSULTA está desactivado',
  ])('treats "%s" as FORBIDDEN (access denied)', (message) => {
    expect(classifyError(message)).toBe('FORBIDDEN')
  })

  it.each([
    'fromDate no puede ser posterior a toDate',
    `Variable '$from' has invalid value: Value cannot represent a Date: "2026-13-30". month must be in 1..12`,
  ])('treats "%s" as BAD_USER_INPUT', (message) => {
    expect(classifyError(message)).toBe('BAD_USER_INPUT')
  })

  it('keeps login failures and unknown messages as UNKNOWN so the form shows them verbatim', () => {
    expect(classifyError('Correo o contraseña incorrectos')).toBe('UNKNOWN')
    expect(classifyError('Algo inesperado')).toBe('UNKNOWN')
  })
})
