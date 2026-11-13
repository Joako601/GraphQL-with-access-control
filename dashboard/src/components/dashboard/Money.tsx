import { cn } from '@/lib/utils'
import { formatMoney } from '@/lib/format'

/** Renders a server Decimal string as "$1,600.00" / "-$200.00" without float conversion. */
export function Money({ value, className }: { value: string; className?: string }) {
  const formatted = formatMoney(value)
  const text = formatted.startsWith('-') ? `-$${formatted.slice(1)}` : `$${formatted}`
  return <span className={cn('tabular-nums', className)}>{text}</span>
}
