import { createContext, type ReactNode, useContext, useEffect, useState } from 'react'
import type { PageResults } from './api'
import { useAuth } from './auth'

type ChatResultsState = {
  results: PageResults | null
  show: (results: PageResults) => void
  clear: () => void
}

// Saved results remember who asked for them, so they never carry over to another account.
type Saved = { owner: string; results: PageResults }

const STORAGE_KEY = 'cc-chat-results'
const ChatResultsContext = createContext<ChatResultsState | null>(null)

function loadSaved(): Saved | null {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? 'null')
    // Older saves had no owner; treat them as unowned and drop them.
    return saved && typeof saved.owner === 'string' && saved.results ? saved : null
  } catch {
    return null
  }
}

// Holds the latest search results from the chat so they survive opening a product page and coming back.
export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const owner = user ? `user:${user.id}` : 'guest'
  const [saved, setSaved] = useState<Saved | null>(loadSaved)

  // When the logged-in identity changes (log in, log out, switch accounts), drop results that
  // belong to someone else. Waits for the auth check so a page reload keeps your own results.
  useEffect(() => {
    if (!loading && saved && saved.owner !== owner) {
      sessionStorage.removeItem(STORAGE_KEY)
      setSaved(null)
    }
  }, [loading, owner, saved])

  const value: ChatResultsState = {
    // Hidden until we know who's here, so another user's results never flash on screen.
    results: !loading && saved?.owner === owner ? saved.results : null,
    show: (results) => {
      const next = { owner, results }
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      setSaved(next)
    },
    clear: () => {
      sessionStorage.removeItem(STORAGE_KEY)
      setSaved(null)
    },
  }
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside ChatResultsProvider')
  return ctx
}
