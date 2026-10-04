import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { askChat, fetchProduct, formatPrice, type ProductDetail } from '../api'

const LOW_STOCK = 5

// Approximate swatch colors for the catalogue's color names (matched on the last known word).
const SWATCHES: Record<string, string> = {
  navy: '#1f2a44', blue: '#2f5fa7', white: '#ffffff', black: '#1d1d1d', gray: '#9a9a9a', grey: '#9a9a9a',
  charcoal: '#45484d', red: '#b3261e', green: '#2f7a4f', yellow: '#f2c230', gold: '#c9a227', orange: '#e07b2a',
  maroon: '#6d1f2b', purple: '#6a3d9a', pink: '#f2a1b7', coral: '#e8846f', brown: '#7a5233', tan: '#d2b48c',
  cream: '#f3ead6', ivory: '#fbf7e6', silver: '#c0c0c0', teal: '#2a8c8c', burgundy: '#7a1f33', olive: '#6b6b2e', khaki: '#c3b091',
}

function swatch(name: string): string {
  const words = name.toLowerCase().split(/[\s-]+/).reverse()
  const hit = words.find((w) => SWATCHES[w])
  if (!hit) return 'conic-gradient(#b3261e, #1b5e3f, #f2c230, #2f5fa7, #b3261e)'
  return name.toLowerCase().includes('heather') ? `linear-gradient(135deg, ${SWATCHES[hit]}, #c9c9c9)` : SWATCHES[hit]
}

export default function ProductPage() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    fetchProduct(productId).then(setProduct, (e: Error) => setError(e.message))
  }, [productId])

  if (error) return <p className="error">Couldn't find that product: {error}</p>
  if (!product) return <p>Fetching it from the back room…</p>

  return (
    <>
      <Link to="/products" className="back-link">
        ← Back to products
      </Link>
      <div className="product-detail">
        <div className="product-detail-stage">
          <img src={product.image_url} alt={product.name} className="product-detail-image" />
        </div>
        <div className="product-detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price large">{formatPrice(product.price)}</p>
          <p>{product.description}</p>

          <h2>Colors</h2>
          <ul className="color-swatches">
            {product.colors.map((c) => (
              <li key={c}>
                <i style={{ background: swatch(c) }} />
                {c}
              </li>
            ))}
          </ul>

          <h2>Sizes &amp; stock</h2>
          <ul className="size-list">
            {product.inventory.map(({ size, quantity }) => (
              <li key={size} className={quantity === 0 ? 'out' : quantity <= LOW_STOCK ? 'low' : ''}>
                <strong>{size}</strong>
                <span>{quantity === 0 ? 'Sold out' : quantity <= LOW_STOCK ? `Only ${quantity} left` : `${quantity} in stock`}</span>
              </li>
            ))}
          </ul>

          <div className="product-actions">
            <button type="button" className="button" onClick={() => askChat('Do you have this in size ', false)}>
              💬 Ask about this item
            </button>
            <button type="button" className="button secondary" onClick={() => askChat('Show me similar items that are in stock')}>
              Find similar in-stock items
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
