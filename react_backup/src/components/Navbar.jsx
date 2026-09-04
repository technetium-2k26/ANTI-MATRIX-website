import { useState, useEffect } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { Menu, X, Lock, LogOut, User } from 'lucide-react'
import Logo from './Logo.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { isLoggedIn, user, logout } = useAuth()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const navItems = [
    { to: '/',          label: 'Home'     },
    { to: '/about',     label: 'About'    },
    { to: '/services',  label: 'Services' },
    { to: '/pricing',   label: 'Pricing', protected: true },
    { to: '/careers',   label: 'Careers'  },
    { to: '/contact',   label: 'Contact'  },
  ]

  const isActive = (to) => {
    if (to === '/') return location.pathname === '/'
    return location.pathname.startsWith(to)
  }

  return (
    <>
      <nav className={`navbar${scrolled ? ' scrolled' : ''}`} role="navigation" aria-label="Main navigation">
        <div className="container">
          {/* Logo */}
          <Logo light={true} size="md" />

          {/* Desktop links */}
          <ul className="nav-links" role="list">
            {navItems.map(item => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === '/'}
                  className={isActive(item.to) ? 'active' : ''}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                >
                  {item.label}
                  {item.protected && !isLoggedIn && (
                    <Lock size={12} color="var(--color-primary-light)" style={{ opacity: 0.8 }} />
                  )}
                </NavLink>
              </li>
            ))}
          </ul>

          {/* Desktop actions */}
          <div className="nav-actions">
            {isLoggedIn ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--color-primary-light)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <User size={14} /> {user?.name || 'Member'}
                </span>
                <button
                  onClick={logout}
                  className="btn btn-outline btn-sm"
                  style={{ gap: '6px' }}
                >
                  <LogOut size={14} /> Log Out
                </button>
              </div>
            ) : (
              <>
                <Link to="/login" className="btn btn-ghost btn-sm">Log In</Link>
                <Link to="/signup" className="btn btn-primary btn-sm">Get Started</Link>
              </>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            className="nav-toggle"
            onClick={() => setMobileOpen(o => !o)}
            aria-expanded={mobileOpen}
            aria-controls="mobile-nav"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </nav>

      {/* Mobile nav */}
      <div
        id="mobile-nav"
        className={`mobile-nav${mobileOpen ? ' open' : ''}`}
        aria-hidden={!mobileOpen}
      >
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={isActive(item.to) ? 'active' : ''}
          >
            {item.label}
          </NavLink>
        ))}
        <div className="mobile-nav-divider"></div>
        <div className="mobile-nav-actions">
          {isLoggedIn ? (
            <button onClick={logout} className="btn btn-outline btn-sm" style={{justifyContent:'center'}}>
              <LogOut size={14} /> Log Out ({user?.name || 'Member'})
            </button>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline btn-sm" style={{justifyContent:'center'}}>Log In</Link>
              <Link to="/signup" className="btn btn-primary btn-sm" style={{justifyContent:'center'}}>Get Started</Link>
            </>
          )}
        </div>
      </div>
    </>
  )
}
