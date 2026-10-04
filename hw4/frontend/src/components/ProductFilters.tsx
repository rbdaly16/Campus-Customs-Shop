import { type Product, SIZES } from '../api'

export const CATEGORIES = [
  { value: 'hoodie', label: 'Hoodies' },
  { value: 'crewneck', label: 'Crewnecks' },
  { value: 't-shirt', label: 'T-shirts' },
  { value: 'quarter-zip', label: 'Quarter-zips' },
  { value: 'jacket', label: 'Jackets & fleece' },
  { value: 'long-sleeve shirt', label: 'Long-sleeve' },
]

export const SORTS = [
  { value: 'name', label: 'Name (A–Z)' },
  { value: 'price-asc', label: 'Price: low to high' },
  { value: 'price-desc', label: 'Price: high to low' },
]

export type Filters = { q: string; category: string; size: string; sort: string }

export function applyFilters(products: Product[], f: Filters): Product[] {
  const words = f.q.toLowerCase().split(/\s+/).filter(Boolean)
  const matches = products.filter((p) => {
    if (f.category && p.category !== f.category) return false
    if (f.size && !p.sizes_in_stock?.includes(f.size)) return false
    const text = [p.name, p.garment_type, p.description, ...p.colors, ...p.search_tags].join(' ').toLowerCase()
    return words.every((w) => text.includes(w))
  })
  if (f.sort === 'price-asc') return matches.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
  if (f.sort === 'price-desc') return matches.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
  return matches.sort((a, b) => a.name.localeCompare(b.name))
}

type Props = {
  filters: Filters
  counts: Record<string, number>
  shown: number
  total: number
  onChange: (next: Partial<Filters>) => void
  onClear: () => void
}

export default function ProductFilters({ filters, counts, shown, total, onChange, onClear }: Props) {
  const active = Boolean(filters.q || filters.category || filters.size || filters.sort !== 'name')
  return (
    <div className="filters" role="search">
      <div className="filters-row">
        <input
          type="search"
          className="filters-search"
          placeholder="Search hoodies, colleges, colors, sports…"
          aria-label="Search products"
          value={filters.q}
          onChange={(e) => onChange({ q: e.target.value })}
        />
        <label className="filters-select">
          <span>In stock in</span>
          <select value={filters.size} onChange={(e) => onChange({ size: e.target.value })} aria-label="Size in stock">
            <option value="">Any size</option>
            {SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="filters-select">
          <span>Sort</span>
          <select value={filters.sort} onChange={(e) => onChange({ sort: e.target.value })} aria-label="Sort products">
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="filters-chips" role="group" aria-label="Category">
        <button type="button" className={`chip ${filters.category ? '' : 'active'}`} onClick={() => onChange({ category: '' })}>
          All <span>{total}</span>
        </button>
        {CATEGORIES.map((c) => (
          <button
            key={c.value}
            type="button"
            className={`chip ${filters.category === c.value ? 'active' : ''}`}
            aria-pressed={filters.category === c.value}
            onClick={() => onChange({ category: filters.category === c.value ? '' : c.value })}
          >
            {c.label} <span>{counts[c.value] ?? 0}</span>
          </button>
        ))}
      </div>
      <p className="filters-summary" aria-live="polite">
        Showing <strong>{shown}</strong> of {total} items
        {active && (
          <button type="button" className="link-button" onClick={onClear}>
            Clear filters
          </button>
        )}
      </p>
    </div>
  )
}
