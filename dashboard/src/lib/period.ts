export interface Period {
  fromDate: string
  toDate: string
}

// Demo period from the course data set (Banco / Caja / Ahorro).
export const DEFAULT_PERIOD: Period = { fromDate: '2026-10-26', toDate: '2026-10-30' }

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/

function isValidIsoDate(value: string): boolean {
  if (!ISO_DATE_RE.test(value)) return false
  const [y, m, d] = value.split('-').map(Number)
  const date = new Date(Date.UTC(y, m - 1, d))
  return date.getUTCFullYear() === y && date.getUTCMonth() === m - 1 && date.getUTCDate() === d
}

/** Returns a user-facing error message, or null when the period can be sent to the API. */
export function validatePeriod({ fromDate, toDate }: Period): string | null {
  if (!fromDate || !toDate) return 'Selecciona ambas fechas.'
  if (!isValidIsoDate(fromDate) || !isValidIsoDate(toDate)) return 'Alguna de las fechas no es válida.'
  // ISO dates compare correctly as strings.
  if (fromDate > toDate) return 'La fecha inicial no puede ser posterior a la fecha final.'
  return null
}
