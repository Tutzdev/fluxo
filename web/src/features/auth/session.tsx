import { useQueryClient } from '@tanstack/react-query'
import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from 'react'
import { api, connectSession } from '@/lib/api'
import type { Session, User } from '@/lib/types'

const STORAGE_KEY = 'fluxo.session'

interface SessionContextValue {
  user: User | null
  signIn: (email: string, password: string) => Promise<void>
  signUp: (name: string, email: string, password: string) => Promise<void>
  startDemo: () => Promise<void>
  signOut: () => Promise<void>
}

const SessionContext = createContext<SessionContextValue | null>(null)

function readStoredSession(): Session | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    const session = stored ? (JSON.parse(stored) as Session) : null
    return session && new Date(session.expires_at) > new Date() ? session : null
  } catch {
    return null
  }
}

function storeSession(session: Session | null) {
  try {
    if (session) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  } catch {
    // Private windows can refuse storage; the session then lasts until the tab closes.
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [session, setSession] = useState<Session | null>(readStoredSession)

  const replaceSession = useCallback(
    (next: Session | null) => {
      storeSession(next)
      setSession(next)
      queryClient.clear()
    },
    [queryClient],
  )

  // Set during render, not in an effect, so the first queries already carry the token.
  connectSession(
    () => session?.token ?? null,
    () => replaceSession(null),
  )

  const value = useMemo<SessionContextValue>(
    () => ({
      user: session?.user ?? null,
      signIn: async (email, password) => {
        replaceSession(await api<Session>('/api/auth/login', { body: { email, password } }))
      },
      signUp: async (name, email, password) => {
        replaceSession(await api<Session>('/api/auth/register', { body: { name, email, password } }))
      },
      startDemo: async () => {
        replaceSession(await api<Session>('/api/demo/session', { method: 'POST' }))
      },
      signOut: async () => {
        await api('/api/auth/logout', { method: 'POST' }).catch(() => undefined)
        replaceSession(null)
      },
    }),
    [session, replaceSession],
  )

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext)
  if (!context) {
    throw new Error('useSession must be used inside SessionProvider')
  }
  return context
}
