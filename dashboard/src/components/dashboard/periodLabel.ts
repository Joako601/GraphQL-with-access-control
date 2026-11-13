import { formatDate } from '@/lib/format'

/** Period text built from the dates the server returned, so labels always match the data. */
export function periodLabel(fromDate: string, toDate: string): string {
  return `${formatDate(fromDate)} – ${formatDate(toDate)}`
}
