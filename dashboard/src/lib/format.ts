// Server sends Decimal values as strings ("1600.00"). We never parse them to float:
// formatting is pure string manipulation so the displayed digits are exactly the server's.
const DECIMAL_RE = /^([+-]?)(\d*)(?:\.(\d*))?$/

/** "1234567.5" -> "1,234,567.50"; "-200.00" -> "-200.00". Unparseable input is returned as-is. */
export function formatMoney(value: string): string {
  const match = DECIMAL_RE.exec(value.trim())
  if (!match || (match[2] === '' && !match[3])) return value
  const [, sign, intRaw, fracRaw = ''] = match
  const int = intRaw.replace(/^0+(?=\d)/, '') || '0'
  // Contract guarantees 2 decimals; extra digits (if any) are truncated, never rounded via float.
  const frac = fracRaw.padEnd(2, '0').slice(0, 2)
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  const negative = sign === '-' && /[1-9]/.test(int + frac)
  return `${negative ? '-' : ''}${grouped}.${frac}`
}

/** True when the decimal string is strictly below zero ("-0.00" is not negative). */
export function isNegative(value: string): boolean {
  return formatMoney(value).startsWith('-')
}

/** True when the decimal string represents zero ("0.00", "-0.00", "0"). */
export function isZero(value: string): boolean {
  return /^[+-]?0*(\.0*)?$/.test(value.trim())
}

const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

/** "2026-10-26" -> "26 oct 2026" without Date objects (avoids timezone shifts). */
export function formatDate(iso: string): string {
  const [year, month, day] = iso.split('-')
  const name = MONTHS[Number(month) - 1]
  if (!year || !name || !day) return iso
  return `${Number(day)} ${name} ${year}`
}
