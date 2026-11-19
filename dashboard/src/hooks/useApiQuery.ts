import { useCallback, useEffect, useState } from 'react'
import { ApiError } from '@/lib/graphql'

export type QueryState<T> =
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: ApiError }

export function toApiError(err: unknown): ApiError {
  return err instanceof ApiError ? err : new ApiError('Ocurrió un error inesperado.', 'UNKNOWN')
}

/**
 * Runs one GraphQL read and keeps the last answer. `reload` re-queries the server (after a mutation the table is
 * read again, rows are never patched by hand). An UNAUTHENTICATED error ends the session: no half-drawn table.
 * `fetcher` must be stable (useCallback). To query another entity (another account) remount with `key`.
 */
export function useApiQuery<T>(fetcher: () => Promise<T>, onUnauthenticated: () => void) {
  const [state, setState] = useState<QueryState<T>>({ status: 'loading' })
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let current = true // only the latest request may update the screen
    fetcher().then(
      (data) => { if (current) setState({ status: 'success', data }) },
      (err: unknown) => {
        if (!current) return
        const error = toApiError(err)
        if (error.code === 'UNAUTHENTICATED') onUnauthenticated()
        else setState({ status: 'error', error })
      },
    )
    return () => { current = false }
  }, [fetcher, onUnauthenticated, version])

  const reload = useCallback(() => setVersion((v) => v + 1), [])
  return { state, reload }
}

/** Wraps a mutation: pending flag, the API message on error, and logout on UNAUTHENTICATED. */
export function useMutation(onUnauthenticated: () => void) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = useCallback(async (action: () => Promise<void>): Promise<boolean> => {
    setPending(true)
    setError(null)
    try {
      await action()
      return true
    } catch (err) {
      const apiError = toApiError(err)
      if (apiError.code === 'UNAUTHENTICATED') onUnauthenticated()
      else setError(apiError.message)
      return false
    } finally {
      setPending(false)
    }
  }, [onUnauthenticated])

  return { run, pending, error, clearError: useCallback(() => setError(null), []) }
}
