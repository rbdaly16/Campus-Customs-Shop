import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { askChat, fetchProducts, type Product } from '../api'
import { useChatResults } from '../chatResults'
import HandsomeDan from '../components/HandsomeDan'
import ProductCard from '../components/ProductCard'
import ProductFilters, { applyFilters, CATEGORIES, type Filters } from '../components/ProductFilters'

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { results, clear } = useChatResults()
  // Filters live in the URL so a filtered view can be shared, bookmarked, or restored with Back.
  const [params, setParams] = useSearchParams()
  const filters: Filters = {
    q: params.get('q') ?? '',
    category: params.get('category') ?? '',
    size: params.get('size') ?? '',
    sort: params.get('sort') ?? 'name',
  }

  useEffect(() => {
    fetchProducts().then(setProducts, (e: Error) => setError(e.message))
  }, [])

  function updateFilters(next: Partial<Filters>) {
    const merged = { ...filters, ...next }
    const clean = Object.fromEntries(
      Object.entries(merged).filter(([k, v]) => v && !(k === 'sort' && v === 'name')),
    )
    setParams(clean, { replace: true })
  }

  const paramKey = params.toString()
  const shown = useMemo(
    () => (products ? applyFilters([...products], filters) : []),
    // filters is rebuilt from params on every render; paramKey is its stable identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [products, paramKey],
  )
  const counts = useMemo(
    () => Object.fromEntries(CATEGORIES.map((c) => [c.value, products?.filter((p) => p.category === c.value).length ?? 0])),
    [products],
  )

  return (
    <>
      {results && (
        <section className="chat-results" aria-live="polite" id="chat-results">
          <header className="chat-results-header">
            <div>
              <p className="eyebrow">From your chat</p>
              <h1>
                {results.title} <span className="count">· {results.products.length} items</span>
              </h1>
            </div>
            <button type="button" className="nav-button chat-results-clear" onClick={clear}>
              Clear results
            </button>
          </header>
          <div className="product-grid">
            {results.products.map((p, i) => (
              <ProductCard
                index={i}
                key={p.product_id}
                productId={p.product_id}
                name={p.name}
                price={p.price}
                imageUrl={p.image_url}
                description={p.short_description}
              />
            ))}
          </div>
        </section>
      )}

      {results ? (
        <h2 className="section-heading">All products</h2>
      ) : (
        <header className="products-banner">
          <div>
            <p className="eyebrow" style={{ color: '#a9cdfa' }}>The full roster</p>
            <h1>Shop Campus Customs</h1>
            <p>Hoodies, crewnecks, tees, and quarter-zips, all officially licensed. Filter by your size below.</p>
          </div>
          <HandsomeDan size={86} mood="smile" />
        </header>
      )}
      {error && <p className="error">Couldn't load products: {error}</p>}
      {!products && !error && <p>Lacing up the cleats…</p>}
      {products && (
        <>
          <ProductFilters
            filters={filters}
            counts={counts}
            shown={shown.length}
            total={products.length}
            onChange={updateFilters}
            onClear={() => setParams({}, { replace: true })}
          />
          {shown.length === 0 ? (
            <div className="empty-state">
              <HandsomeDan size={90} />
              <p>No products match those filters. (And no, we don't carry anything crimson.) Our assistant might know a close match.</p>
              <button
                type="button"
                className="button"
                onClick={() => askChat(`Can you help me find ${filters.q || 'something'}${filters.size ? ` in size ${filters.size}` : ''}?`)}
              >
                Ask the shop assistant
              </button>
            </div>
          ) : (
            <div className="product-grid">
              {shown.map((p, i) => (
                <ProductCard
                  index={i}
                  key={p.product_id}
                  productId={p.product_id}
                  name={p.name}
                  price={p.price}
                  imageUrl={p.image_url}
                  description={p.description}
                  soldOut={p.sizes_in_stock?.length === 0}
                />
              ))}
            </div>
          )}
        </>
      )}
    </>
  )
}
