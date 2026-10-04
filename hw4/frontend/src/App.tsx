import { Link, Route, Routes, useLocation } from 'react-router-dom'
import ChatWidget from './components/ChatWidget'
import DanCursor, { useDanCursorSetting } from './components/DanCursor'
import HandsomeDan from './components/HandsomeDan'
import NavBar from './components/NavBar'
import About from './pages/About'
import CreateAccount from './pages/CreateAccount'
import Home from './pages/Home'
import Login from './pages/Login'
import ProductPage from './pages/ProductPage'
import Products from './pages/Products'

// Only facts we can stand behind: no shipping promises or sale claims.
const TICKER = [
  'Officially licensed Yale apparel',
  '57 Broadway · New Haven, CT',
  'Hoodies · Crewnecks · Tees · Quarter-zips · Jackets',
  'Sizes XS–XXL',
  'Residential college gear',
  'Proudly 0% crimson',
  'Questions? Ask Dan, our shop assistant',
]

function Marquee() {
  // Rendered twice so the strip loops seamlessly.
  return (
    <div className="marquee" aria-label="Store highlights">
      <div className="marquee-track">
        {[...TICKER, ...TICKER].map((t, i) => (
          <span key={i} aria-hidden={i >= TICKER.length}>
            {t}
          </span>
        ))}
      </div>
    </div>
  )
}

function Footer() {
  const [danOn, setDanOn] = useDanCursorSetting()
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <HandsomeDan size={44} mood="smile" />
          <div>
            <strong>Campus Customs</strong>
            <small>Officially licensed Yale apparel · 57 Broadway, New Haven, CT</small>
          </div>
        </div>
        <label className="footer-toggle">
          <input type="checkbox" checked={danOn} onChange={(e) => setDanOn(e.target.checked)} />
          Handsome Dan follows my cursor
        </label>
      </div>
    </footer>
  )
}

function NotFound() {
  return (
    <div className="empty-state">
      <HandsomeDan size={110} />
      <h1>That page wandered off the pitch.</h1>
      <p className="muted">Even Handsome Dan couldn't sniff it out. Maybe it transferred to Harvard.</p>
      <Link to="/products" className="button">
        Back to the shop
      </Link>
    </div>
  )
}

export default function App() {
  const location = useLocation()
  return (
    <>
      <NavBar />
      <Marquee />
      {/* Keyed by path so each page fades in when you navigate. */}
      <main className="page page-enter" key={location.pathname}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductPage />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      <ChatWidget />
      <DanCursor />
    </>
  )
}
