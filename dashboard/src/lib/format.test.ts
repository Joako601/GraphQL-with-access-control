import { describe, expect, it } from 'vitest'
import { formatDate, formatMoney, isNegative, isZero } from './format'

describe('formatMoney', () => {
  it.each([
    ['1600.00', '1,600.00'],
    ['0.00', '0.00'],
    ['500.00', '500.00'],
    ['1000000.5', '1,000,000.50'],
    ['1234567.89', '1,234,567.89'],
    ['999', '999.00'],
    ['1000', '1,000.00'],
    ['-200.00', '-200.00'],
    ['-1234.5', '-1,234.50'],
    ['-0.00', '0.00'],
    ['+3500.00', '3,500.00'],
    ['0001500.10', '1,500.10'],
    ['.5', '0.50'],
    ['12345678901234567890.12', '12,345,678,901,234,567,890.12'],
    ['10.999', '10.99'],
  ])('formats %s as %s', (input, expected) => {
    expect(formatMoney(input)).toBe(expected)
  })

  it('returns unparseable input unchanged', () => {
    expect(formatMoney('abc')).toBe('abc')
    expect(formatMoney('')).toBe('')
    expect(formatMoney('1,000.00')).toBe('1,000.00')
  })
})

describe('isNegative / isZero', () => {
  it('detects negatives without float math', () => {
    expect(isNegative('-200.00')).toBe(true)
    expect(isNegative('-0.00')).toBe(false)
    expect(isNegative('300.00')).toBe(false)
  })

  it('detects zero values', () => {
    expect(isZero('0.00')).toBe(true)
    expect(isZero('-0.00')).toBe(true)
    expect(isZero('0.01')).toBe(false)
  })
})

describe('formatDate', () => {
  it('formats ISO dates in Spanish without timezone shifts', () => {
    expect(formatDate('2026-10-26')).toBe('26 oct 2026')
    expect(formatDate('2026-01-01')).toBe('1 ene 2026')
  })
})
