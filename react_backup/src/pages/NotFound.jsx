import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="not-found">
      <div className="container" style={{textAlign:'center'}}>
        <h1>404</h1>
        <h2 style={{color:'var(--color-text)', marginBottom:'var(--space-md)'}}>Page not found</h2>
        <p style={{marginBottom:'var(--space-2xl)', maxWidth:'480px', margin:'0 auto var(--space-2xl)'}}>
          The page you're looking for doesn't exist or has been moved. Let's get you back on track.
        </p>
        <div style={{display:'flex', justifyContent:'center', gap:'var(--space-md)', flexWrap:'wrap'}}>
          <Link to="/" className="btn btn-primary btn-lg">
            Go Home <ArrowRight size={17} />
          </Link>
          <Link to="/contact" className="btn btn-outline btn-lg">
            Contact Support
          </Link>
        </div>
      </div>
    </div>
  )
}
