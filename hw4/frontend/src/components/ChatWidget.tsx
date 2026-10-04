import { type FormEvent, useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { type ChatMessage, fetchChatHistory, formatPrice, type PageResults, sendChatMessage } from '../api'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'
import HandsomeDan, { type DanMood } from './HandsomeDan'

type Bubble = Pick<ChatMessage, 'role' | 'content' | 'products' | 'page_results'> & { key: string }

const greeting = (name: string | null): Bubble => ({
  key: 'greeting',
  role: 'assistant',
  content: name
    ? `Welcome back, ${name}! I'm Dan, the Campus Customs helper. Ask me about hoodies, sizes, or whatever's on your mind.`
    : "Howdy, friend! I'm Dan, the Campus Customs helper. Ask me about hoodies, sizes, or whatever's on your mind.",
  products: [],
})

// Rotating status lines while Dan fetches an answer. Friendly rivalry only.
const FETCHING_LINES = [
  'Sniffing through the racks…',
  'Checking the stockroom. No crimson back there, promise…',
  'Fetching faster than Harvard leaves The Game at halftime…',
  'Asking Handsome Dan. He says Boola Boola…',
  'Consulting the playbook Harvard wishes it had…',
]

// One-tap starter questions that fit the page the shopper is on.
function quickQuestions(path: string): string[] {
  if (path.startsWith('/products/')) {
    return ['What sizes are in stock?', 'What colors does this come in?', 'Show me similar items']
  }
  if (path === '/products') return ['Show me hoodies', "What's under $40?", 'Anything for Branford College?']
  return ["What's good for game day?", 'Show me hoodies', 'Gift ideas for a Yale parent']
}

export default function ChatWidget() {
  const { user, loading } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const chatResults = useChatResults()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Bubble[]>([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [danMood, setDanMood] = useState<DanMood>('neutral')
  const [fetchLine, setFetchLine] = useState(0)
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Load the conversation whenever who's logged in changes: saved history for customers,
  // this server session's messages for guests.
  useEffect(() => {
    if (loading) return
    setMessages([greeting(user?.first_name ?? null)])
    setError(null)
    fetchChatHistory().then(
      (history) =>
        setMessages([greeting(user?.first_name ?? null), ...history.map((m) => ({ ...m, key: String(m.id) }))]),
      (e: Error) => setError(e.message),
    )
  }, [user, loading])

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' })
  }, [messages, sending, open])

  // Start on a random quip, then rotate every couple of seconds while waiting.
  useEffect(() => {
    if (!sending) return
    setFetchLine(Math.floor(Math.random() * FETCHING_LINES.length))
    const id = setInterval(() => setFetchLine((i) => (i + 1) % FETCHING_LINES.length), 2200)
    return () => clearInterval(id)
  }, [sending])

  // On wide screens the page makes room for the open panel so no product card sits underneath it.
  useEffect(() => {
    document.body.classList.toggle('chat-open', open)
    return () => document.body.classList.remove('chat-open')
  }, [open])

  // Put search matches on the Products page and bring them into view; the chat stays open.
  function showOnPage(results: PageResults) {
    chatResults.show(results)
    if (location.pathname !== '/products') navigate('/products')
    // Wait a tick so the Products page has mounted after navigating.
    setTimeout(() => document.getElementById('chat-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || sending) return
    setDraft('')
    setError(null)
    setMessages((m) => [...m, { key: `pending-${Date.now()}`, role: 'user', content: text, products: [] }])
    setSending(true)
    try {
      const reply = await sendChatMessage(text, location.pathname)
      setMessages((m) => [...m, { ...reply, key: `reply-${reply.id}-${Date.now()}` }])
      if (reply.page_results) showOnPage(reply.page_results)
      // Dan gives a happy lick when an answer lands.
      setDanMood('lick')
      setTimeout(() => setDanMood('smile'), 700)
      setTimeout(() => setDanMood('neutral'), 2200)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSending(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    send(draft)
  }

  // Other parts of the site (e.g. "Ask about this item") open the chat via askChat().
  const sendRef = useRef(send)
  sendRef.current = send
  useEffect(() => {
    function onAsk(e: Event) {
      const { text, send: autoSend } = (e as CustomEvent<{ text: string; send: boolean }>).detail
      setOpen(true)
      if (autoSend) sendRef.current(text)
      else {
        setDraft(text)
        setTimeout(() => inputRef.current?.focus(), 50)
      }
    }
    window.addEventListener('cc-chat-ask', onAsk)
    return () => window.removeEventListener('cc-chat-ask', onAsk)
  }, [])

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Chat with Campus Customs">
          <header className="chat-header">
            <div className="chat-header-who">
              <HandsomeDan size={40} mood={sending ? 'neutral' : danMood} />
              <div>
                <strong>Ask Dan</strong>
                <small>{sending ? 'Fetching…' : 'Campus Customs shop assistant'}</small>
              </div>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>

          {!user && (
            <p className="chat-guest-note">
              Chatting as a guest. <Link to="/login" onClick={() => setOpen(false)}>Log in</Link> to save this
              conversation for next time.
            </p>
          )}
          <div className="chat-messages">
            {messages.map((m) => (
              <div key={m.key} className={`chat-row ${m.role}`}>
                {m.role === 'assistant' && <HandsomeDan size={30} />}
                <div className={`chat-bubble ${m.role}`}>
                  {m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : m.content}
                  {m.page_results && (
                    <button type="button" className="chat-page-link" onClick={() => showOnPage(m.page_results!)}>
                      View all {m.page_results.products.length} on the page →
                    </button>
                  )}
                  {m.products.length > 0 && (
                    <div className="chat-cards">
                      {m.products.map((p) => (
                        <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-card">
                          <img src={p.image_url} alt="" />
                          <span className="chat-card-name">{p.name}</span>
                          <span className="price">{formatPrice(p.price)}</span>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="chat-row assistant typing" aria-label="Dan is typing">
                <HandsomeDan size={30} />
                <div className="chat-bubble assistant chat-typing">
                  <span className="paws">
                    <span>🐾</span>
                    <span>🐾</span>
                    <span>🐾</span>
                  </span>
                  <em key={fetchLine} className="chat-fetch-line">
                    {FETCHING_LINES[fetchLine]}
                  </em>
                </div>
              </div>
            )}
            {error && <p className="chat-error">{error}</p>}
            <div ref={endRef} />
          </div>
          {!sending && (
            <div className="chat-quick" aria-label="Suggested questions">
              {quickQuestions(location.pathname).map((q) => (
                <button key={q} type="button" className="chip" onClick={() => send(q)}>
                  {q}
                </button>
              ))}
            </div>
          )}
          <form className="chat-form" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask about products, sizes, stock…"
              aria-label="Message"
              maxLength={2000}
            />
            <button type="submit" disabled={!draft.trim() || sending}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className={`chat-toggle ${open ? 'open' : ''}`}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open chat with Dan, the shop assistant'}
      >
        {open ? (
          'Close'
        ) : (
          <>
            <HandsomeDan size={42} mood="smile" /> Ask Dan
          </>
        )}
      </button>
    </div>
  )
}
