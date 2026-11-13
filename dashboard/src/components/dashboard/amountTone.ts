import { isNegative } from '@/lib/format'

// Course rule: a negative balance (money below zero) must not look like a negative profit
// (a loss in the period). Balance below zero = red + "En rojo" badge; loss = amber text only.
export function balanceClass(value: string): string {
  return isNegative(value) ? 'text-red-400' : ''
}

export function profitClass(value: string): string {
  return isNegative(value) ? 'text-warning' : ''
}
