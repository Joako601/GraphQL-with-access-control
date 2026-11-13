// Session lives only in sessionStorage (cleared when the tab closes), never in localStorage or code.
const SESSION_KEY = 'dashboard.session'

/** Minimal user data returned by `login { user { id name email } }`. */
export interface SessionUser {
  id: string
  name: string
  email: string
}

export interface Session {
  token: string
  user: SessionUser
}

export function readSession(): Session | null {
  try {
    const session = JSON.parse(sessionStorage.getItem(SESSION_KEY) ?? 'null') as Session | null
    return session?.token && session.user ? session : null
  } catch {
    return null
  }
}

export function saveSession(session: Session): void {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function clearSession(): void {
  sessionStorage.removeItem(SESSION_KEY)
}
