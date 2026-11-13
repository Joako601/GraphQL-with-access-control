import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { fetchCompanyName, fetchGeneralBalance, type GeneralBalance } from '@/lib/api'
import { ApiError } from '@/lib/graphql'
import type { Period } from '@/lib/period'

export type BalanceState =
  | { status: 'loading' }
  | { status: 'success'; data: GeneralBalance }
  | { status: 'error'; error: ApiError }

function toApiError(err: unknown): ApiError {
  if (err instanceof ApiError) return err
  return new ApiError('Ocurrió un error inesperado.', 'UNKNOWN')
}

/** Loads the company name once and `generalBalance` on demand. Any UNAUTHENTICATED error ends the session. */
export function useDashboardData(token: string, initialPeriod: Period, onUnauthenticated: () => void) {
  const [companyName, setCompanyName] = useState<string | null>(null)
  const [balance, setBalance] = useState<BalanceState>({ status: 'loading' })
  // Guards against out-of-order responses: only the latest request may update the screen.
  const requestId = useRef(0)
  const lastPeriod = useRef(initialPeriod)

  const load = useCallback(
    async (period: Period) => {
      const id = ++requestId.current
      lastPeriod.current = period
      setBalance({ status: 'loading' })
      try {
        const data = await fetchGeneralBalance(token, period)
        if (id === requestId.current) setBalance({ status: 'success', data })
      } catch (err) {
        if (id !== requestId.current) return
        const error = toApiError(err)
        if (error.code === 'UNAUTHENTICATED') return onUnauthenticated()
        setBalance({ status: 'error', error })
      }
    },
    [token, onUnauthenticated],
  )

  const retry = useCallback(() => load(lastPeriod.current), [load])

  useEffect(() => {
    fetchCompanyName(token)
      .then(setCompanyName)
      .catch((err: unknown) => {
        const error = toApiError(err)
        if (error.code === 'UNAUTHENTICATED') return onUnauthenticated()
        // Non-fatal: only the company name is missing; the balance request reports its own errors.
        toast.error('No se pudo cargar el nombre de la empresa.', { description: error.message })
      })
    void load(lastPeriod.current)
  }, [token, load, onUnauthenticated])

  return { companyName, balance, load, retry }
}
