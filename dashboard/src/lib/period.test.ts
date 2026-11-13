import { describe, expect, it } from 'vitest'
import { validatePeriod, type Period } from './period'

const period = (fromDate: string, toDate: string): Period => ({ fromDate, toDate })

describe('validatePeriod', () => {
  it('accepts a valid range', () => {
    expect(validatePeriod(period('2026-10-26', '2026-10-30'))).toBeNull()
  })

  it('accepts a single-day range', () => {
    expect(validatePeriod(period('2026-10-26', '2026-10-26'))).toBeNull()
  })

  it('rejects fromDate after toDate', () => {
    expect(validatePeriod(period('2026-10-31', '2026-10-30'))).toMatch(/posterior/)
  })

  it('rejects ranges crossing years in the wrong order', () => {
    expect(validatePeriod(period('2027-01-01', '2026-12-31'))).toMatch(/posterior/)
  })

  it('rejects missing dates', () => {
    expect(validatePeriod(period('', '2026-10-30'))).toMatch(/ambas/)
    expect(validatePeriod(period('2026-10-26', ''))).toMatch(/ambas/)
  })

  it('rejects malformed or impossible dates', () => {
    expect(validatePeriod(period('2026-02-30', '2026-03-01'))).toMatch(/válida/)
    expect(validatePeriod(period('26/10/2026', '2026-10-30'))).toMatch(/válida/)
  })
})
