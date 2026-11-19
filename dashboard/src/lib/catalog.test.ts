import { describe, expect, it } from 'vitest'
import type { CompanyUser } from './admin'
import { accountReference, accountTypeLabel, can, countUsers, filterUsers, formatJoinedAt } from './catalog'
import { parseRoute, routeHref } from './route'

function user(name: string, email: string, extra: Partial<CompanyUser> = {}): CompanyUser {
  return { id: email, isAdmin: false, isActive: true, joinedAt: '2026-11-18T00:00:00+00:00',
    user: { name, email }, role: null, ...extra }
}

const USERS = [
  user('Joaquín Uriona', 'joaquin.uriona@equipo.test', { isAdmin: true }),
  user('Mateo Tec', 'mateo.tec@equipo.test'),
  user('Ariff Medina', 'ariff.medina@equipo.test'),
  user('Fernando Castro', 'fernando.castro@equipo.test', { isActive: false }),
]

describe('countUsers', () => {
  it('cuenta activos, administrador principal e inactivos con la misma lista', () => {
    expect(countUsers(USERS)).toEqual({ active: 3, admins: 1, inactive: 1 })
  })
  it('no oculta un segundo administrador (error de datos)', () => {
    expect(countUsers([...USERS, user('Otro', 'otro@x.test', { isAdmin: true })]).admins).toBe(2)
  })
  it('empresa sin membresías', () => {
    expect(countUsers([])).toEqual({ active: 0, admins: 0, inactive: 0 })
  })
})

describe('filterUsers', () => {
  it('busca por nombre sin acentos ni mayúsculas', () => {
    expect(filterUsers(USERS, 'JOAQUIN', 'all').map((u) => u.user.name)).toEqual(['Joaquín Uriona'])
  })
  it('busca por correo', () => {
    expect(filterUsers(USERS, 'ariff.medina@', 'all')).toHaveLength(1)
  })
  it('filtra por estado', () => {
    expect(filterUsers(USERS, '', 'active')).toHaveLength(3)
    expect(filterUsers(USERS, '', 'inactive').map((u) => u.user.name)).toEqual(['Fernando Castro'])
  })
})

describe('cuentas', () => {
  it('muestra la etiqueta y no el código crudo', () => {
    expect(accountTypeLabel('CASH')).toBe('Efectivo')
    expect(accountTypeLabel('WALLET')).toBe('Monedero')
  })
  it('enmascara la referencia', () => {
    expect(accountReference({ maskedClabe: '****1234', cardLastDigits: null })).toBe('****1234')
    expect(accountReference({ maskedClabe: null, cardLastDigits: '9876' })).toBe('****9876')
    expect(accountReference({ maskedClabe: null, cardLastDigits: null })).toBeNull()
  })
})

describe('permisos y fechas', () => {
  it('can revisa el código exacto', () => {
    expect(can(['accounts.read'], 'accounts.write')).toBe(false)
    expect(can(['accounts.read', 'accounts.write'], 'accounts.write')).toBe(true)
  })
  it('formatJoinedAt usa la zona local, no la fecha UTC', () => {
    expect(formatJoinedAt('2026-11-18T12:00:00+00:00')).toBe('18 nov 2026')
    const tarde = new Date(2026, 10, 18, 20, 30) // 20:30 locales; en México ya es el 19 en UTC
    expect(formatJoinedAt(tarde.toISOString())).toBe('18 nov 2026')
    expect(formatJoinedAt('no-es-fecha')).toBe('no-es-fecha')
  })
})

describe('route', () => {
  it('lee el módulo administrativo del hash', () => {
    expect(parseRoute('#/admin/cuentas')).toEqual({ section: 'admin', module: 'cuentas' })
    expect(parseRoute('#/admin/otra')).toEqual({ section: 'admin', module: 'usuarios' })
  })
  it('sin hash abre el dashboard financiero de la actividad 1', () => {
    expect(parseRoute('')).toEqual({ section: 'financiero' })
    expect(routeHref({ section: 'admin', module: 'conceptos' })).toBe('#/admin/conceptos')
  })
})
