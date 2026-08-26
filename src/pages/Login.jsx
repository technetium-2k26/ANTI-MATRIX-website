import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Eye, EyeOff, ArrowLeft } from 'lucide-react'
import Logo from '../components/Logo.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function validate(form) {
  const errors = {}
  if (!form.email.trim())                    errors.email    = 'Email is required'
  else if (!/\S+@\S+\.\S+/.test(form.email)) errors.email   = 'Enter a valid email address'
  if (!form.password)                        errors.password = 'Password is required'
  else if (form.password.length < 6)         errors.password = 'Password must be at least 6 characters'
  return errors
}

export default function Login() {
  const [form, setForm]     = useState({ email:'', password:'', remember: false })
  const [errors, setErrors] = useState({})
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const redirectPath = searchParams.get('redirect') || '/pricing'

  useEffect(() => { document.title = 'Log In | Anti-Matrix' }, [])

  const set = k => e => setForm(f => ({...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value}))

  const handleSubmit = async e => {
    e.preventDefault()
    const errs = validate(form)
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    setLoading(true)
    await new Promise(r => setTimeout(r, 800))
    login({ email: form.email, name: form.email.split('@')[0] })
    setLoading(false)
    setSuccess(true)
    setTimeout(() => {
      navigate(redirectPath)
    }, 900)
  }

  return (
    <div className="auth-page">
      <div className="auth-card animate-fade-up">
        <Link to="/" className="back-link">
          <ArrowLeft size={15} /> Back to Anti-Matrix
        </Link>

        <div style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
          <Logo light={true} size="lg" stacked={true} />
        </div>

        {success ? (
          <div style={{textAlign:'center', padding:'var(--space-xl) 0'}}>
            <div style={{fontSize:'3rem', marginBottom:'var(--space-md)'}}>✓</div>
            <h2 style={{marginBottom:'var(--space-sm)'}}>Welcome back!</h2>
            <p>You've successfully logged in. Redirecting you to your dashboard...</p>
          </div>
        ) : (
          <>
            <h2>Welcome back</h2>
            <p className="auth-subtitle">Sign in to your Anti-Matrix account</p>

            <form className="auth-form" onSubmit={handleSubmit} noValidate aria-label="Login form">
              <div className="form-group">
                <label htmlFor="login-email">Email Address</label>
                <input
                  id="login-email" type="email"
                  className={`form-control${errors.email ? ' error' : ''}`}
                  placeholder="you@company.com"
                  value={form.email} onChange={set('email')}
                  autoComplete="email" aria-required="true"
                  aria-describedby={errors.email ? 'login-email-err' : undefined}
                />
                {errors.email && <span id="login-email-err" className="form-error">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="login-password">Password</label>
                <div className="password-field">
                  <input
                    id="login-password"
                    type={showPw ? 'text' : 'password'}
                    className={`form-control${errors.password ? ' error' : ''}`}
                    placeholder="Your password"
                    value={form.password} onChange={set('password')}
                    autoComplete="current-password" aria-required="true"
                    aria-describedby={errors.password ? 'login-pw-err' : undefined}
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowPw(p => !p)} aria-label={showPw ? 'Hide password' : 'Show password'}>
                    {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
                {errors.password && <span id="login-pw-err" className="form-error">{errors.password}</span>}
              </div>

              <div className="auth-extras">
                <label className="checkbox-label">
                  <input type="checkbox" checked={form.remember} onChange={set('remember')} />
                  Remember me
                </label>
                <a href="#forgot" className="auth-link">Forgot password?</a>
              </div>

              <button type="submit" className="btn btn-primary w-full" style={{justifyContent:'center'}} disabled={loading}>
                {loading ? 'Signing in…' : 'Sign In'}
              </button>
            </form>

            <p className="auth-switch">
              Don't have an account?
              <Link to="/signup" className="auth-link"> Create one free</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
