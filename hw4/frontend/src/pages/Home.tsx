import { useEffect, useState } from 'react'
import type React from 'react'
import { Link } from 'react-router-dom'
import { askChat, fetchProducts, type Product } from '../api'
import HandsomeDan from '../components/HandsomeDan'
import ProductCard from '../components/ProductCard'
import { CATEGORIES } from '../components/ProductFilters'

// Hand-picked game-day lineup; only shown if still in the catalogue.
const PICKS = [
  '2025-yale-vs-harvard-t-shirt',
  'champion-reverse-weave-hoodie-1',
  'branford-1-4-zip',
  'district-vit-crewneck-vintage-bulldog',
]

const VALUES = [
  {
    title: 'Rep your residential college',
    body: 'Branford, Berkeley, Davenport, Benjamin Franklin, and the whole gang. Every college deserves its own fan club, and we’re happy to be the merch table.',
  },
  {
    title: 'Game-day ready',
    body: 'Yale vs. Harvard is the kind of rivalry that puts a little extra hop in your step. Our tees and crewnecks make sure folks can spot you in the stands.',
  },
  {
    title: 'Something for everybody',
    body: 'Students, grads, moms, dads, aunts, uncles, and the neighbor who just loves a good bulldog. If you’ve got Blue in your heart, there’s a size here for you.',
  },
]

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])
  useEffect(() => {
    fetchProducts().then(setProducts, () => setProducts([]))
  }, [])

  const categories = CATEGORIES.map((c) => {
    const inCategory = products.filter((p) => p.category === c.value)
    return { ...c, count: inCategory.length, image: inCategory.find((p) => p.sizes_in_stock?.length)?.image_url }
  }).filter((c) => c.count > 0)
  const picks = PICKS.map((id) => products.find((p) => p.product_id === id)).filter((p): p is Product => !!p)

  return (
    <>
      <section className="hero">
        <div>
          <p className="eyebrow">Officially licensed Yale apparel · New Haven, CT</p>
          <h1>
            Big Pride, Big Yale, and <em>Even Bigger Hugs</em>
          </h1>
          <p className="lead">
            Well, hey there, friend! Welcome to Campus Customs. We’ve got hoodies cozier than a biscuit fresh out of
            the oven, tees that’ll cheer louder than the student section, and quarter-zips for folks who like to look
            sharp and stay warm at the same time. Casual comfort, classic Bulldog pride. That’s the whole playbook.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="button">
              Shop the collection →
            </Link>
            <button type="button" className="button ghost" onClick={() => askChat("What's good for game day?")}>
              💬 Ask Dan what's hot
            </button>
          </div>
        </div>
        <div className="hero-mascot" aria-hidden="true">
          <div className="hero-badge">
            <svg className="hero-badge-ring" viewBox="0 0 300 300">
              <defs>
                <path id="ring" d="M150,150 m-127,0 a127,127 0 1,1 254,0 a127,127 0 1,1 -254,0" />
              </defs>
              <text>
                <textPath href="#ring">CAMPUS CUSTOMS ★ HANDSOME DAN APPROVED ★ NEW HAVEN ★</textPath>
              </text>
            </svg>
            <HandsomeDan size={200} mood="smile" />
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Find your fit</p>
            <h2>Shop by category</h2>
          </div>
          <Link to="/products">See everything →</Link>
        </div>
        <div className="category-grid">
          {categories.map((c, i) => (
            <Link
              key={c.value}
              to={`/products?category=${encodeURIComponent(c.value)}`}
              className="category-tile"
              style={{ '--i': i } as React.CSSProperties}
            >
              {c.image && <img src={c.image} alt="" loading="lazy" />}
              <span className="category-tile-label">
                <strong>{c.label}</strong>
                <span>{c.count} styles</span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      {picks.length > 0 && (
        <section className="section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Coach’s lineup</p>
              <h2>Game-day picks</h2>
            </div>
            <Link to="/products?sort=price-asc">Shop by price →</Link>
          </div>
          <div className="product-grid">
            {picks.map((p, i) => (
              <ProductCard
                key={p.product_id}
                index={i}
                productId={p.product_id}
                name={p.name}
                price={p.price}
                imageUrl={p.image_url}
                description={p.description}
                soldOut={p.sizes_in_stock?.length === 0}
              />
            ))}
          </div>
        </section>
      )}

      <section className="section feature-grid">
        {VALUES.map((v, i) => (
          <article key={v.title} className="feature" style={{ '--i': i } as React.CSSProperties}>
            <h2>{v.title}</h2>
            <p>{v.body}</p>
          </article>
        ))}
      </section>
    </>
  )
}
