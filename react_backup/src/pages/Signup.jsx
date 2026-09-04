import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, ArrowLeft, CheckCircle2 } from 'lucide-react'
import Logo from '../components/Logo.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function validate(form) {
  const errors = {}
  if (!form.name.trim())                       errors.name    = 'Full name is required'
  if (!form.email.trim())                      errors.email   = 'Email is required'
  else if (!/\S+@\S+\.\S+/.test(form.email))  errors.email   = 'Enter a valid email address'
  if (!form.password)                          errors.password = 'Password is required'
  else if (form.password.length < 8)           errors.password = 'Password must be at least 8 characters'
  if (!form.confirm)                           errors.confirm  = 'Please confirm your password'
  else if (form.confirm !== form.password)     errors.confirm  = 'Passwords do not match'
  if (!form.terms)                             errors.terms   = 'You must accept the terms to continue'
  return errors
}

const benefits = [
  'Free consultation with our experts',
  'Access to project dashboard & pricing',
  'Priority support & updates',
  'Dedicated account manager',
]

export default function Signup() {
  const [form, setForm]     = useState({ name:'', email:'', password:'', confirm:'', terms: false })
  const [errors, setErrors] = useState({})
  const [showPw, setShowPw] = useState(false)
  const [showC,  setShowC]  = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()

  useEffect(() => { document.title = 'Create Account | Anti-Matrix' }, [])

  const set = k => e => setForm(f => ({...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value}))

  const handleSubmit = async e => {
    e.preventDefault()
    const errs = validate(form)
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    setLoading(true)
    await new Promise(r => setTimeout(r, 800))
    login({ name: form.name, email: form.email })
    setLoading(false)
    setSuccess(true)
    setTimeout(() => {
      navigate('/pricing')
    }, 1200)
  }

  return (
    <div className="auth-page" style={{alignItems:'flex-start', paddingTop:'calc(var(--nav-height) + 2rem)'}}>
      <div className="auth-card animate-fade-up" style={{maxWidth:'520px'}}>
        <Link to="/" className="back-link">
          <ArrowLeft size={15} /> Back to Anti-Matrix
        </Link>

        <div style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
          <Logo light={true} size="lg" stacked={true} />
        </div>

        {success ? (
          <div style={{textAlign:'center', padding:'var(--space-xl) 0'}}>
            <div style={{
              width:'64px', height:'64px', background:'var(--color-primary-glow)',
              borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center',
              margin:'0 auto var(--space-lg)', border:'2px solid rgba(34,197,94,0.4)'
            }}>
              <CheckCircle2 size={28} color="var(--color-primary-light)" />
            </div>
            <h2 style={{marginBottom:'var(--space-sm)'}}>Account created!</h2>
            <p style={{marginBottom:'var(--space-xl)'}}>
              Welcome to Anti-Matrix, {form.name.split(' ')[0]}! We've sent a confirmation email to <strong style={{color:'var(--color-text)'}}>{form.email}</strong>. Check your inbox to get started.
            </p>
            <Link to="/login" className="btn btn-primary" style={{justifyContent:'center', width:'100%'}}>
              Go to Login
            </Link>
          </div>
        ) : (
          <>
            <h2>Create your account</h2>
            <p className="auth-subtitle">Join Anti-Matrix and start building something great</p>

            {/* Benefits */}
            <div style={{
              background:'rgba(22,163,74,0.06)', border:'1px solid rgba(22,163,74,0.2)',
              borderRadius:'var(--radius-md)', padding:'var(--space-lg)',
              marginBottom:'var(--space-xl)', display:'flex', flexDirection:'column', gap:'0.5rem'
            }}>
              {benefits.map(b => (
                <div key={b} style={{display:'flex', alignItems:'center', gap:'0.5rem'}}>
                  <CheckCircle2 size={14} color="var(--color-primary-light)" />
                  <span style={{fontSize:'0.875rem', color:'var(--color-text-muted)'}}>{b}</span>
                </div>
              ))}
            </div>

            <form className="auth-form" onSubmit={handleSubmit} noValidate aria-label="Sign up form">
              <div className="form-group">
                <label htmlFor="signup-name">Full Name</label>
                <input
                  id="signup-name" type="text"
                  className={`form-control${errors.name ? ' error' : ''}`}
                  placeholder="John Smith"
                  value={form.name} onChange={set('name')}
                  autoComplete="name" aria-required="true"
                />
                {errors.name && <span className="form-error">{errors.name}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="signup-email">Email Address</label>
                <input
                  id="signup-email" type="email"
                  className={`form-control${errors.email ? ' error' : ''}`}
                  placeholder="you@company.com"
                  value={form.email} onChange={set('email')}
                  autoComplete="email" aria-required="true"
                />
                {errors.email && <span className="form-error">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="signup-password">Password</label>
                <div className="password-field">
                  <input
                    id="signup-password"
                    type={showPw ? 'text' : 'password'}
                    className={`form-control${errors.password ? ' error' : ''}`}
                    placeholder="Minimum 8 characters"
                    value={form.password} onChange={set('password')}
                    autoComplete="new-password" aria-required="true"
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowPw(p => !p)} aria-label={showPw ? 'Hide password' : 'Show password'}>
                    {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
                {errors.password && <span className="form-error">{errors.password}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="signup-confirm">Confirm Password</label>
                <div className="password-field">
                  <input
                    id="signup-confirm"
                    type={showC ? 'text' : 'password'}
                    className={`form-control${errors.confirm ? ' error' : ''}`}
                    placeholder="Repeat your password"
                    value={form.confirm} onChange={set('confirm')}
                    autoComplete="new-password" aria-required="true"
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowC(p => !p)} aria-label={showC ? 'Hide confirm password' : 'Show confirm password'}>
                    {showC ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
                {errors.confirm && <span className="form-error">{errors.confirm}</span>}
              </div>

              <div className="form-group">
                <label className="checkbox-label" style={{alignItems:'flex-start', gap:'0.625rem'}}>
                  <input
                    type="checkbox"
                    checked={form.terms} onChange={set('terms')}
                    style={{marginTop:'2px'}}
                    aria-required="true"
                  />
                  <span>
                    I agree to Anti-Matrix's{' '}
                    <Link to="/terms" className="auth-link">Terms of Service</Link>
                    {' '}and{' '}
                    <Link to="/privacy" className="auth-link">Privacy Policy</Link>
                  </span>
                </label>
                {errors.terms && <span className="form-error" style={{marginTop:'0.25rem'}}>{errors.terms}</span>}
              </div>

              <button type="submit" className="btn btn-primary w-full" style={{justifyContent:'center'}} disabled={loading}>
                {loading ? 'Creating account…' : 'Create Account'}
              </button>
            </form>

            <p className="auth-switch">
              Already have an account?
              <Link to="/login" className="auth-link"> Sign in</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
