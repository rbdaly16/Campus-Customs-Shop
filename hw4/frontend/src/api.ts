export type Product = {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  // Only on the list endpoint (GET /api/products).
  sizes_in_stock?: string[]
  category?: string
}

export const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL'] as const

// Opens the chat panel and sends a question, from anywhere on the site.
export function askChat(text: string, send = true) {
  window.dispatchEvent(new CustomEvent('cc-chat-ask', { detail: { text, send } }))
}

export type StockLevel = { size: string; quantity: number }

export type ProductDetail = Product & { inventory: StockLevel[] }

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

export type User = { id: number; first_name: string; last_name: string; email: string; member_since: string }

export type RegisterInput = { first_name: string; last_name: string; email: string; password: string }

// FastAPI returns `detail` as a string for our errors and as a list for validation errors.
async function errorMessage(res: Response): Promise<string> {
  const body = await res.json().catch(() => null)
  const detail = body?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg).replace(/^Value error, /, '')
  return `${res.status} ${res.statusText}`
}

async function postJson<T>(url: string, data?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: data === undefined ? undefined : JSON.stringify(data),
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return (res.status === 204 ? undefined : await res.json()) as T
}

export const register = (input: RegisterInput) => postJson<User>('/api/auth/register', input)

export const login = (email: string, password: string) =>
  postJson<User>('/api/auth/login', { email, password })

export const logout = () => postJson<void>('/api/auth/logout')

export async function fetchCurrentUser(): Promise<User | null> {
  const res = await fetch('/api/auth/me')
  return res.ok ? res.json() : null
}

export type ProductCard = Pick<Product, 'product_id' | 'name' | 'garment_type' | 'price' | 'image_url'> & {
  short_description: string
}

// Catalogue matches the agent chose to show on the page (not just in the chat bubble).
export type PageResults = { title: string; products: ProductCard[] }

export type ChatMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
  products: ProductCard[]
  page_results?: PageResults | null
  created_at: string
}

export async function fetchChatHistory(): Promise<ChatMessage[]> {
  const res = await fetch('/api/chat/history')
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json()
}

// Only the path is sent; the server works out the page (and product) from it.
export const sendChatMessage = (message: string, pagePath: string) =>
  postJson<ChatMessage>('/api/chat', { message, page_path: pagePath })

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

export function shortDescription(text: string, max = 110): string {
  const firstSentence = text.split(/(?<=\.)\s/)[0]
  return firstSentence.length <= max ? firstSentence : `${firstSentence.slice(0, max).trimEnd()}…`
}
