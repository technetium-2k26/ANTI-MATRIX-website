import { Link } from 'react-router-dom'
import { Mail, MapPin, Phone, ArrowRight, Zap } from 'lucide-react'
import Logo from './Logo.jsx'

/* Simple social SVG icons */
const SocialIcon = ({ label, children }) => (
  <a href="#" target="_blank" rel="noopener noreferrer" aria-label={label} className="footer-social-link"
    style={{width:'38px',height:'38px',display:'flex',alignItems:'center',justifyContent:'center',
    border:'1px solid var(--color-border)',borderRadius:'var(--radius-sm)',color:'var(--color-text-dim)',
    transition:'all 0.25s',textDecoration:'none'}}
    onMouseEnter={e => { e.currentTarget.style.borderColor='var(--color-primary)'; e.currentTarget.style.color='var(--color-primary-light)'; e.currentTarget.style.background='var(--color-primary-glow)' }}
    onMouseLeave={e => { e.currentTarget.style.borderColor='var(--color-border)'; e.currentTarget.style.color='var(--color-text-dim)'; e.currentTarget.style.background='transparent' }}
  >
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">{children}</svg>
  </a>
)

export default function Footer({ showCta = true }) {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="footer-wrapper" aria-label="Site footer">
      <div className="container">
        
        {/* Seamless Integrated CTA Section */}
        {showCta && (
          <div className="cta-section reveal">
            <div className="badge" style={{ margin: '0 auto var(--space-md)' }}>
              <Zap size={13} /> Let's Build Together
            </div>
            <h2>Ready to transform your digital future?</h2>
            <p>Tell us your vision and we'll engineer the perfect technology solution for your business.</p>
            <div className="cta-actions">
              <Link to="/contact" className="btn btn-primary btn-lg">
                Start Your Project <ArrowRight size={17} />
              </Link>
              <Link to="/pricing" className="btn btn-outline btn-lg">
                Explore Pricing Plans
              </Link>
            </div>
          </div>
        )}

        {/* Main Footer Links & Info */}
        <div className="footer">
          <div className="footer-grid">

            {/* Brand column */}
            <div className="footer-brand">
              <div style={{ marginBottom: 'var(--space-md)' }}>
                <Logo light={true} size="md" />
              </div>
              <p>
                Empowering modern enterprises through innovative software, AI models, and scalable cloud systems.
              </p>
              <div className="footer-social" style={{display:'flex', gap:'var(--space-sm)'}}>
                <SocialIcon label="LinkedIn">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </SocialIcon>
                <SocialIcon label="Twitter/X">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.253 5.622 5.911-5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </SocialIcon>
                <SocialIcon label="GitHub">
                  <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
                </SocialIcon>
                <SocialIcon label="YouTube">
                  <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </SocialIcon>
              </div>
            </div>

            {/* Company links */}
            <div className="footer-col">
              <h4>Company</h4>
              <ul className="footer-links">
                <li><Link to="/about">About Us</Link></li>
                <li><Link to="/services">Services</Link></li>
                <li><Link to="/pricing">Pricing</Link></li>
                <li><Link to="/careers">Careers</Link></li>
                <li><Link to="/contact">Contact</Link></li>
              </ul>
            </div>

            {/* Resources */}
            <div className="footer-col">
              <h4>Resources</h4>
              <ul className="footer-links">
                <li><Link to="/pricing">Pricing Plans</Link></li>
                <li><Link to="/services">Our Services</Link></li>
                <li><Link to="/about">Our Story</Link></li>
                <li><Link to="/privacy">Privacy Policy</Link></li>
                <li><Link to="/terms">Terms of Service</Link></li>
              </ul>
            </div>

            {/* Contact */}
            <div className="footer-col">
              <h4>Contact</h4>
              <div className="footer-contact-item">
                <Mail size={15} color="var(--color-primary-light)" />
                <span>contact@anti-matrix.com</span>
              </div>
              <div className="footer-contact-item">
                <Phone size={15} color="var(--color-primary-light)" />
                <span>+1 (555) 000-1234</span>
              </div>
              <div className="footer-contact-item">
                <MapPin size={15} color="var(--color-primary-light)" />
                <span>San Francisco, CA<br />United States</span>
              </div>
            </div>

          </div>

          {/* Bottom bar */}
          <div className="footer-bottom">
            <p>© {currentYear} Anti-Matrix. All rights reserved.</p>
            <div className="footer-bottom-links">
              <Link to="/privacy">Privacy Policy</Link>
              <Link to="/terms">Terms of Service</Link>
              <Link to="/contact">Support</Link>
            </div>
          </div>
        </div>

      </div>
    </footer>
  )
}
