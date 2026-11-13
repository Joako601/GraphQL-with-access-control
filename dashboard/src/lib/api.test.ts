import { describe, expect, it } from 'vitest'
import { companyIdFromToken } from './api'
import { ApiError } from './graphql'

/** Builds an unsigned token with the same payload shape as services/auth.py (signature is irrelevant here). */
function tokenWith(payload: object): string {
  const b64url = (value: object) => btoa(JSON.stringify(value)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
  return `${b64url({ alg: 'HS256', typ: 'JWT' })}.${b64url(payload)}.firma`
}

describe('companyIdFromToken', () => {
  it('reads companyId from the JWT payload', () => {
    expect(companyIdFromToken(tokenWith({ companyUserId: 40, companyId: 32, exp: 1 }))).toBe('32')
  })

  it('decodes base64url payloads that need padding', () => {
    expect(companyIdFromToken(tokenWith({ companyId: 7, name: 'ñ?>' }))).toBe('7')
  })

  it.each(['basura', 'a.b.c', tokenWith({ companyUserId: 1 })])('rejects "%s" as an invalid session', (token) => {
    expect(() => companyIdFromToken(token)).toThrow(ApiError)
    try {
      companyIdFromToken(token)
    } catch (err) {
      expect((err as ApiError).code).toBe('UNAUTHENTICATED')
    }
  })
})
