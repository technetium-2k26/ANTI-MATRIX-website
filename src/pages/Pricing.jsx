import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, ArrowRight, Zap } from 'lucide-react'

const plans = [
  {
    tier: 'Starter',
    name: 'Starter Package',
    price: '2,499',
    period: 'project',
    desc: 'Perfect for small businesses and startups needing a professional digital presence.',
    features: [
      'Up to 5-page website or mobile app MVP',
      'Custom UI/UX design',
      'Responsive across all devices',
      'Basic SEO setup',
      'Contact form & integrations',
      'Google Analytics setup',
      '30-day post-launch support',
      '2 revision rounds',
    ],
    notIncluded: ['Custom backend / API', 'AI/ML features', 'Dedicated project manager'],
    cta: 'Get Started',
    ctaLink: '/contact',
    featured: false,
  },
  {
    tier: 'Growth',
    name: 'Growth Package',
    price: '7,999',
    period: 'project',
    desc: 'For growing businesses that need a robust digital platform with advanced functionality.',
    features: [
      'Full web application or mobile app',
      'Custom backend API & database',
      'User authentication & roles',
      'Third-party integrations (CRM, payments)',
      'Admin dashboard',
      'SEO & performance optimization',
      'CI/CD deployment pipeline',
      '90-day post-launch support',
      'Dedicated project manager',
      '5 revision rounds',
    ],
    notIncluded: ['AI/ML features', 'Full DevOps setup'],
    cta: 'Start Your Project',
    ctaLink: '/contact',
    featured: true,
  },
  {
    tier: 'Enterprise',
    name: 'Enterprise Package',
    price: 'Custom',
    period: '',
    desc: 'Full-scale digital transformation with AI, cloud infrastructure, and ongoing partnership.',
    features: [
      'Everything in Growth, plus:',
      'AI/ML system design & deployment',
      'Cloud infrastructure (AWS/GCP/Azure)',
      'Microservices architecture',
      'Custom enterprise integrations',
      'Security audit & penetration testing',
      'Dedicated engineering team',
      '12-month support & maintenance',
      'Quarterly business reviews',
      'SLA with uptime guarantees',
    ],
    notIncluded: [],
    cta: 'Contact Sales',
    ctaLink: '/contact',
    featured: false,
  },
]

const retainerPlans = [
  {
    name: 'Essential',
    price: '1,499',
    desc: 'Up to 20 hours/month',
    features: ['Bug fixes & updates', 'Minor feature additions', 'Performance monitoring', 'Monthly report'],
  },
  {
    name: 'Professional',
    price: '3,499',
    desc: 'Up to 50 hours/month',
    features: ['Everything in Essential', 'New feature development', 'SEO & content updates', 'Priority support (24h SLA)', 'Bi-weekly check-ins'],
  },
  {
    name: 'Dedicated',
    price: '6,999',
    desc: 'Full-time dedicated engineer',
    features: ['Everything in Professional', 'Unlimited hours', '4h SLA response', 'Weekly strategy calls', 'Architecture reviews', 'Direct Slack access'],
  },
]

const faqs = [
  { q: 'Do you offer a free consultation?', a: 'Yes. Every project starts with a free 30-minute discovery call where we understand your goals and provide tailored recommendations.' },
  { q: 'How long does a typical project take?', a: 'A Starter project typically takes 4–6 weeks. Growth packages are 8–16 weeks. Enterprise engagements are scoped individually based on complexity.' },
  { q: 'Can I upgrade my plan mid-project?', a: 'Absolutely. We structure our projects to be flexible. You can upgrade or expand scope at any point with a simple change order.' },
  { q: 'Do you offer payment plans?', a: 'We offer milestone-based billing: typically 30% upfront, 40% at mid-point, and 30% on delivery. Enterprise clients can negotiate custom payment schedules.' },
  { q: 'What technologies do you specialize in?', a: 'React, Next.js, Node.js, Python, React Native, Flutter, AWS, GCP, TensorFlow, and more. We choose the best technology for each specific problem.' },
]

export default function Pricing() {
  const [openFaq, setOpenFaq] = useState(null)

  useEffect(() => {
    document.title = 'Pricing | Anti-Matrix'
    window.scrollTo(0, 0)
    const els = document.querySelectorAll('.reveal')
    const io = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); io.unobserve(e.target) } }),
      { threshold: 0.1 }
    )
    els.forEach(el => io.observe(el))
    return () => io.disconnect()
  }, [])

  return (
    <>
      <section className="page-hero">
        <div className="container">
          <div className="badge"><Zap size={11} /> Transparent Pricing</div>
          <h1>Simple, honest pricing for every stage of growth</h1>
          <p>No hidden fees. No surprises. Just clear investment in technology that delivers results.</p>
        </div>
      </section>

      {/* Project Packages */}
      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container">
          <div className="section-header centered">
            <h2 style={{color:'var(--color-white)'}}>Project Packages</h2>
            <div className="divider center"></div>
            <p>One-time investment packages for new digital products. All prices in USD.</p>
          </div>

          <div className="pricing-grid">
            {plans.map(plan => (
              <div key={plan.name} className={`pricing-card${plan.featured ? ' featured' : ''}`}>
                {plan.featured && <div className="pricing-badge">Most Popular</div>}
                <div className="pricing-header">
                  <div className="pricing-tier">{plan.tier}</div>
                  <div className="pricing-name">{plan.name}</div>
                  <div className="pricing-price">
                    {plan.price !== 'Custom' && <span className="pricing-currency">$</span>}
                    <span className="pricing-amount">{plan.price}</span>
                    {plan.period && <span style={{fontSize:'0.875rem', color:'var(--color-text-dim)', marginLeft:'4px'}}>/{plan.period}</span>}
                  </div>
                  <p className="pricing-desc">{plan.desc}</p>
                </div>
                <ul className="pricing-features">
                  {plan.features.map(f => (
                    <li key={f}>
                      <CheckCircle2 size={15} />
                      {f}
                    </li>
                  ))}
                </ul>
                <div className="pricing-footer">
                  <Link to={plan.ctaLink} className={`btn ${plan.featured ? 'btn-primary' : 'btn-outline'}`}>
                    {plan.cta} <ArrowRight size={15} />
                  </Link>
                </div>
              </div>
            ))}
          </div>

          <p style={{textAlign:'center', marginTop:'var(--space-2xl)', color:'var(--color-text-dim)', fontSize:'0.875rem'}}>
            All projects include NDA, IP ownership transfer, and source code delivery.
          </p>
        </div>
      </section>

      {/* Monthly Retainer */}
      <section className="section reveal" style={{background:'var(--color-bg-alt)'}}>
        <div className="container">
          <div className="section-header centered">
            <div className="badge">Ongoing Support</div>
            <h2 style={{color:'var(--color-white)'}}>Monthly Retainer Plans</h2>
            <div className="divider center"></div>
            <p>Keep your product growing with dedicated ongoing engineering and support. Per month, minimum 3 months.</p>
          </div>

          <div className="pricing-grid">
            {retainerPlans.map((plan, i) => (
              <div key={plan.name} className={`pricing-card${i === 1 ? ' featured' : ''}`}>
                {i === 1 && <div className="pricing-badge">Best Value</div>}
                <div className="pricing-header">
                  <div className="pricing-name">{plan.name}</div>
                  <div className="pricing-price">
                    <span className="pricing-currency">$</span>
                    <span className="pricing-amount">{plan.price}</span>
                    <span style={{fontSize:'0.875rem', color:'var(--color-text-dim)', marginLeft:'4px'}}>/mo</span>
                  </div>
                  <p className="pricing-desc">{plan.desc}</p>
                </div>
                <ul className="pricing-features">
                  {plan.features.map(f => (
                    <li key={f}><CheckCircle2 size={15} />{f}</li>
                  ))}
                </ul>
                <div className="pricing-footer">
                  <Link to="/contact" className={`btn ${i === 1 ? 'btn-primary' : 'btn-outline'}`}>
                    Get Started <ArrowRight size={15} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container" style={{maxWidth:'760px', margin:'0 auto'}}>
          <div className="section-header centered">
            <h2 style={{color:'var(--color-white)'}}>Frequently Asked Questions</h2>
            <div className="divider center"></div>
          </div>

          <div style={{display:'flex', flexDirection:'column', gap:'var(--space-sm)'}}>
            {faqs.map((faq, i) => (
              <div key={i} style={{
                border:'1px solid',
                borderColor: openFaq === i ? 'rgba(22,163,74,0.3)' : 'var(--color-border)',
                borderRadius:'var(--radius-md)',
                overflow:'hidden',
                background: openFaq === i ? 'rgba(22,163,74,0.04)' : 'rgba(255,255,255,0.02)',
                transition:'all 0.25s'
              }}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{
                    width:'100%', textAlign:'left', padding:'var(--space-lg) var(--space-xl)',
                    background:'none', border:'none', color:'var(--color-text)', cursor:'pointer',
                    fontFamily:'var(--font-heading)', fontWeight:600, fontSize:'1rem',
                    display:'flex', justifyContent:'space-between', alignItems:'center', gap:'var(--space-md)'
                  }}
                  aria-expanded={openFaq === i}
                >
                  {faq.q}
                  <span style={{
                    color:'var(--color-primary-light)', fontSize:'1.25rem', flexShrink:0,
                    transform: openFaq === i ? 'rotate(45deg)' : 'none', transition:'transform 0.25s'
                  }}>+</span>
                </button>
                {openFaq === i && (
                  <div style={{padding:'0 var(--space-xl) var(--space-lg)'}}>
                    <p>{faq.a}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section reveal">
        <div className="container">
          <h2>Can't find what you need?</h2>
          <p>Every project is unique. Let's discuss your specific requirements and build a custom proposal.</p>
          <div className="cta-actions">
            <Link to="/contact" className="btn btn-primary btn-lg">Request Custom Quote <ArrowRight size={17} /></Link>
          </div>
        </div>
      </section>
    </>
  )
}
