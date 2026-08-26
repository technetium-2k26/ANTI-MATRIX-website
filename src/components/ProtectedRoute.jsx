import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Lock, ArrowRight, ShieldCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

export default function ProtectedRoute({ children, title = 'Protected Content' }) {
  const { isLoggedIn } = useAuth()
  const location = useLocation()

  if (isLoggedIn) {
    return children
  }

  return (
    <div className="section" style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', background: 'var(--color-bg)' }}>
      <div className="container" style={{ maxWidth: '580px', margin: '0 auto' }}>
        <div className="card text-center animate-fade-up" style={{ padding: 'var(--space-3xl) var(--space-2xl)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <div style={{
            width: '68px',
            height: '68px',
            background: 'var(--color-primary-glow)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto var(--space-lg)',
            color: 'var(--color-primary-light)'
          }}>
            <Lock size={30} />
          </div>

          <div className="badge" style={{ margin: '0 auto var(--space-md)' }}>
            <ShieldCheck size={13} /> Member Access Only
          </div>

          <h2 style={{ color: 'var(--color-white)', marginBottom: 'var(--space-md)' }}>
            Protected Pricing & Plans
          </h2>

          <p style={{ marginBottom: 'var(--space-2xl)', lineHeight: 1.8 }}>
            Our pricing and custom package details are exclusive to registered Anti-Matrix members. Please sign in to unlock access.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <Link
              to={`/login?redirect=${encodeURIComponent(location.pathname)}`}
              className="btn btn-primary btn-lg"
              style={{ justifyContent: 'center' }}
            >
              Sign In to View Pricing <ArrowRight size={17} />
            </Link>

            <Link
              to="/signup"
              className="btn btn-outline"
              style={{ justifyContent: 'center' }}
            >
              Create a Free Account
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
