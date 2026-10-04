import type React from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, shortDescription } from '../api'

type Props = {
  productId: string
  name: string
  price: number
  imageUrl: string
  description: string
  soldOut?: boolean
  index?: number // staggers the entrance animation
}

// Shared by the Products grid and the chat-driven results so both open the same product page.
export default function ProductCard({ productId, name, price, imageUrl, description, soldOut, index = 0 }: Props) {
  return (
    <Link to={`/products/${productId}`} className="product-card" style={{ '--i': index } as React.CSSProperties}>
      {soldOut && <span className="badge sold-out">Sold out</span>}
      <div className="product-card-media">
        <img src={imageUrl} alt={name} loading="lazy" />
        <span className="product-card-view">View details</span>
      </div>
      <div className="product-card-body">
        <h2>{name}</h2>
        <p className="price">{formatPrice(price)}</p>
        <p className="muted">{shortDescription(description)}</p>
      </div>
    </Link>
  )
}
