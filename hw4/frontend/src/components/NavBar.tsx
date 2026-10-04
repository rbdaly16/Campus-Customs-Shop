import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../auth'
import HandsomeDan from './HandsomeDan'

const LINKS = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const GUEST_LINKS = [
  { to: '/login', label: 'Log in' },
  { to: '/create-account', label: 'Create account' },
]

export default function NavBar() {
  const { user, loading, logout } = useAuth()

  return (
    <header className="nav">
      <Link to="/" className="nav-brand" aria-label="Campus Customs home">
        <HandsomeDan size={42} />
        <span className="nav-brand-text">
          <span className="nav-brand-name">Campus Customs</span>
          <span className="nav-brand-tag">Yale apparel · New Haven</span>
        </span>
      </Link>
      <nav className="nav-links">
        {LINKS.map(({ to, label }) => (
          <NavLink key={to} to={to} end={to === '/'}>
            {label}
          </NavLink>
        ))}
        {!loading &&
          (user ? (
            <>
              <span className="nav-user">Hi, {user.first_name}!</span>
              <button type="button" className="nav-button" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            GUEST_LINKS.map(({ to, label }) => (
              <NavLink key={to} to={to}>
                {label}
              </NavLink>
            ))
          ))}
      </nav>
    </header>
  )
}
