import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Target, Eye, Heart, Lightbulb, Users, Award, Globe, CheckCircle2 } from 'lucide-react'

const values = [
  { icon: <Lightbulb size={20} />, title: 'Innovation First', desc: 'We pursue creative, forward-thinking solutions that push boundaries and set new industry standards.' },
  { icon: <Heart size={20} />,     title: 'Client Obsession', desc: 'Everything we do centers around delivering real, lasting value to our clients and their end users.' },
  { icon: <Award size={20} />,     title: 'Uncompromising Quality', desc: 'We hold ourselves to the highest standards in code, design, and communication — no shortcuts.' },
  { icon: <Globe size={20} />,     title: 'Global Perspective', desc: 'A diverse, globally-minded team that understands digital products for a borderless world.' },
]

const team = [
  { initials: 'AP', name: 'Alex Park',       role: 'Chief Executive Officer',    desc: '12+ years leading technology organizations across SaaS, FinTech, and enterprise software.' },
  { initials: 'SR', name: 'Sophia Reynolds', role: 'Chief Technology Officer',   desc: 'Former Google engineer with expertise in distributed systems and AI infrastructure.' },
  { initials: 'MK', name: 'Marcus Kim',      role: 'Head of Design',             desc: 'Award-winning UX designer who has shaped products used by millions of users worldwide.' },
  { initials: 'JL', name: 'Julia Lopez',     role: 'Head of Engineering',        desc: 'Full-stack architect specializing in scalable microservices and cloud-native architecture.' },
  { initials: 'DT', name: 'David Tran',      role: 'Head of AI & Data Science',  desc: 'PhD in ML with 8+ years building production AI systems for Fortune 500 companies.' },
  { initials: 'NW', name: 'Nadia Williams',  role: 'Head of Client Success',     desc: 'Dedicated to building long-term partnerships and ensuring clients achieve their digital goals.' },
]


export default function About() {
  useEffect(() => {
    document.title = 'About Us | Anti-Matrix'
    window.scrollTo(0, 0)
    // Scroll reveal
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
      {/* Page Hero */}
      <section className="page-hero">
        <div className="container">
          <div className="badge"><Award size={11} /> Our Story</div>
          <h1>We build the technology<br />that powers tomorrow</h1>
          <p>Anti-Matrix is a technology company on a mission: to make enterprise-grade software, AI, and cloud infrastructure accessible to every ambitious business.</p>
        </div>
      </section>

      {/* Mission / Vision */}
      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container">
          <div className="about-cols">
            <div>
              <div className="badge"><Target size={11} /> Mission & Vision</div>
              <h2 style={{color:'var(--color-white)', marginBottom:'var(--space-lg)'}}>
                Technology should be a superpower, not a barrier
              </h2>
              <div className="divider"></div>
              <p style={{marginBottom:'var(--space-lg)'}}>
                Our <strong style={{color:'var(--color-text)'}}>mission</strong> is to accelerate digital transformation by delivering technology solutions that are powerful, reliable, and perfectly aligned with each client's unique business goals.
              </p>
              <p style={{marginBottom:'var(--space-xl)'}}>
                Our <strong style={{color:'var(--color-text)'}}>vision</strong> is a world where every organization — from a bootstrapped startup to a global enterprise — has access to the same caliber of digital infrastructure that drives the world's most successful companies.
              </p>
              <div style={{display:'flex', gap:'var(--space-md)', flexWrap:'wrap'}}>
                <div style={{background:'var(--color-primary-glow)', border:'1px solid rgba(34,197,94,0.25)', borderRadius:'var(--radius-md)', padding:'var(--space-lg) var(--space-xl)', flex:'1', minWidth:'160px'}}>
                  <div style={{fontFamily:'var(--font-heading)', fontSize:'2rem', fontWeight:800, color:'var(--color-white)'}}>200+</div>
                  <div style={{fontSize:'0.8125rem', color:'var(--color-text-dim)', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600}}>Projects Delivered</div>
                </div>
                <div style={{background:'var(--color-primary-glow)', border:'1px solid rgba(34,197,94,0.25)', borderRadius:'var(--radius-md)', padding:'var(--space-lg) var(--space-xl)', flex:'1', minWidth:'160px'}}>
                  <div style={{fontFamily:'var(--font-heading)', fontSize:'2rem', fontWeight:800, color:'var(--color-white)'}}>98%</div>
                  <div style={{fontSize:'0.8125rem', color:'var(--color-text-dim)', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600}}>Client Satisfaction</div>
                </div>
              </div>
            </div>

            <div>
              <img
                src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80"
                alt="Anti-Matrix team collaborating in modern office"
                style={{width:'100%', borderRadius:'var(--radius-xl)', objectFit:'cover', height:'400px', border:'1px solid var(--color-border)'}}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="section reveal" style={{background:'var(--color-bg-alt)'}}>
        <div className="container">
          <div className="section-header centered">
            <div className="badge"><Heart size={11} /> Our Values</div>
            <h2 style={{color:'var(--color-white)'}}>The principles that guide us</h2>
            <div className="divider center"></div>
            <p>Everything we build, every team we form, every decision we make flows from these core values.</p>
          </div>
          <div className="values-grid">
            {values.map(v => (
              <div key={v.title} className="value-card">
                <div className="icon-box">{v.icon}</div>
                <h3>{v.title}</h3>
                <p>{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="section reveal" style={{background:'var(--color-bg-alt)'}}>
        <div className="container">
          <div className="section-header centered">
            <div className="badge"><Users size={11} /> Leadership</div>
            <h2 style={{color:'var(--color-white)'}}>Meet the people behind Anti-Matrix</h2>
            <div className="divider center"></div>
            <p>Our leadership team brings decades of combined experience from the world's leading technology organizations.</p>
          </div>
          <div className="board-grid">
            {team.map(m => (
              <div key={m.name} className="board-card">
                <div className="board-avatar">{m.initials}</div>
                <h4>{m.name}</h4>
                <div className="board-role">{m.role}</div>
                <p>{m.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section reveal">
        <div className="container">
          <h2>Ready to build something great together?</h2>
          <p>Let's talk about your project and how Anti-Matrix can help you achieve your goals.</p>
          <div className="cta-actions">
            <Link to="/contact" className="btn btn-primary btn-lg">Start a Conversation <ArrowRight size={17} /></Link>
            <Link to="/careers" className="btn btn-outline btn-lg">Join Our Team</Link>
          </div>
        </div>
      </section>
    </>
  )
}
