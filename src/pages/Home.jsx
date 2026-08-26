import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight, Code2, Smartphone, Brain, TrendingUp, Shield,
  Globe, CheckCircle2, Star, ChevronRight, Zap, Users, Award, Clock
} from 'lucide-react'

/* ── Animate sections on scroll ──────────────────────── */
function useScrollReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal')
    const io = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); io.unobserve(e.target) } }),
      { threshold: 0.12 }
    )
    els.forEach(el => io.observe(el))
    return () => io.disconnect()
  }, [])
}

/* ── Data ─────────────────────────────────────────────── */
const services = [
  {
    icon: <Code2 size={24} />, title: 'Web Development',
    desc: 'Custom, high-performance websites and web applications built for scale and reliability.',
    caps: ['React / Next.js SPAs', 'Full-stack Node & Python APIs', 'E-commerce platforms', 'Progressive Web Apps']
  },
  {
    icon: <Smartphone size={24} />, title: 'Mobile Applications',
    desc: 'Native and cross-platform mobile apps delivering seamless experiences on iOS and Android.',
    caps: ['React Native & Flutter', 'iOS & Android native', 'App Store optimization', 'Push & offline support']
  },
  {
    icon: <Brain size={24} />, title: 'AI & Machine Learning',
    desc: 'Intelligent automation and data-driven insights that give your business a competitive edge.',
    caps: ['Predictive analytics', 'NLP & chatbot solutions', 'Computer vision systems', 'ML model deployment']
  },
  {
    icon: <TrendingUp size={24} />, title: 'Digital Marketing & Growth',
    desc: 'Data-backed strategies that drive targeted traffic, qualified leads, and measurable ROI.',
    caps: ['SEO & content strategy', 'Paid media campaigns', 'Conversion optimization', 'Analytics & reporting']
  },
  {
    icon: <Shield size={24} />, title: 'Cloud & DevOps',
    desc: 'Secure, scalable cloud infrastructure with automated CI/CD pipelines and monitoring.',
    caps: ['AWS / GCP / Azure', 'Docker & Kubernetes', 'CI/CD automation', 'Security & compliance']
  },
  {
    icon: <Globe size={24} />, title: 'UI/UX Design',
    desc: 'Human-centered design that converts visitors into loyal customers through elegant experiences.',
    caps: ['User research & personas', 'Wireframing & prototyping', 'Design systems', 'Accessibility-first']
  },
]

const stats = [
  { value: '200+', label: 'Projects Delivered' },
  { value: '98%',  label: 'Client Satisfaction' },
  { value: '50+',  label: 'Team Members'        },
  { value: '6+',   label: 'Years of Excellence' },
]

const testimonials = [
  {
    initials: 'SM', company: 'ScaleUp Finance', industry: 'FinTech',
    text: 'Anti-Matrix transformed our legacy banking platform into a modern, cloud-native system. The team delivered exceptional quality under a tight deadline — completely exceeded our expectations.',
    stars: 5
  },
  {
    initials: 'LK', company: 'MedCore Health', industry: 'HealthTech',
    text: 'Working with Anti-Matrix was a game-changer. Their AI solution reduced our patient intake time by 60% and their support has been outstanding every step of the way.',
    stars: 5
  },
  {
    initials: 'RJ', company: 'RetailNova', industry: 'E-Commerce',
    text: 'From strategy to launch, Anti-Matrix delivered a full e-commerce ecosystem that scaled Black Friday traffic flawlessly. Revenue up 40% in the first quarter.',
    stars: 5
  },
]

const technologies = [
  'React', 'Node.js', 'Python', 'AWS', 'GCP', 'Docker',
  'Kubernetes', 'TensorFlow', 'PostgreSQL', 'MongoDB', 'Flutter', 'TypeScript'
]

const whyUs = [
  { icon: <Zap size={20} />, title: 'Rapid Delivery', desc: 'Agile sprints with weekly demos so you always see progress and can pivot fast.' },
  { icon: <Shield size={20} />, title: 'Enterprise Security', desc: 'Security-first architecture with SOC 2 practices baked into every project.' },
  { icon: <Users size={20} />, title: 'Dedicated Teams', desc: 'Senior engineers, designers, and PMs assigned exclusively to your project.' },
  { icon: <Award size={20} />, title: 'Proven Quality', desc: '200+ delivered projects with a 98% client satisfaction rate across 6+ years.' },
]

/* ── Component ────────────────────────────────────────── */
export default function Home() {
  useScrollReveal()

  useEffect(() => {
    document.title = 'Anti-Matrix | Enterprise Digital Transformation'
  }, [])

  return (
    <>
      {/* ── HERO ────────────────────────────────────── */}
      <section className="hero" aria-label="Hero">
        <div className="hero-bg">
          <div className="hero-grid"></div>
        </div>
        <div className="container">
          <div className="hero-content animate-fade-up">
            <div className="badge">
              <Zap size={11} /> Enterprise Technology Partner
            </div>
            <h1>
              Build. Scale.<br />
              <span>Transform Your Digital Future</span>
            </h1>
            <p className="hero-subtitle">
              Anti-Matrix is a full-service technology company delivering world-class web, mobile, AI, and cloud solutions. We turn ambitious ideas into scalable digital products.
            </p>
            <div className="hero-actions">
              <Link to="/services" className="btn btn-primary btn-lg">
                Explore Services <ArrowRight size={17} />
              </Link>
              <Link to="/contact" className="btn btn-outline btn-lg">
                Get a Free Consultation
              </Link>
            </div>
          </div>

          <div className="hero-stats animate-fade-up delay-3">
            {stats.map(s => (
              <div key={s.label}>
                <div className="hero-stat-value"><span>{s.value}</span></div>
                <div className="hero-stat-label">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── WHO WE ARE ──────────────────────────────── */}
      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container">
          <div className="about-cols">
            <div>
              <div className="badge"><Award size={11} /> About Anti-Matrix</div>
              <h2 style={{color:'var(--color-white)', marginBottom:'var(--space-lg)'}}>
                We are your long-term technology growth partner
              </h2>
              <div className="divider"></div>
              <p style={{marginBottom:'var(--space-xl)'}}>
                Anti-Matrix is a forward-thinking technology company built by engineers, designers, and strategists who are passionate about solving real business problems with elegant digital solutions.
              </p>
              <p style={{marginBottom:'var(--space-2xl)'}}>
                From early-stage startups to global enterprises, we deliver tailor-made software, AI systems, and digital growth strategies that create measurable impact. Our team of 50+ experts combines deep technical expertise with sharp business thinking.
              </p>
              <Link to="/about" className="btn btn-outline">
                Learn Our Story <ChevronRight size={16} />
              </Link>
            </div>

            <div>
              <div className="about-pillars">
                {[
                  { title: 'Our Mission', desc: 'To accelerate digital transformation through technology that is powerful, elegant, and accessible.' },
                  { title: 'Our Vision',  desc: 'A world where every business — large or small — has access to enterprise-grade technology.' },
                  { title: 'Innovation',  desc: 'We stay at the cutting edge of AI, cloud, and software engineering to future-proof your investment.' },
                  { title: 'Partnership', desc: 'We don\'t just build and leave. We become long-term partners invested in your success.' },
                ].map(p => (
                  <div key={p.title} className="pillar-card">
                    <h4>{p.title}</h4>
                    <p>{p.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── SERVICES ────────────────────────────────── */}
      <section className="section reveal" style={{background:'var(--color-bg-alt)'}}>
        <div className="container">
          <div className="section-header centered">
            <div className="badge"><Code2 size={11} /> What We Build</div>
            <h2 style={{color:'var(--color-white)'}}>End-to-end technology services</h2>
            <div className="divider center"></div>
            <p>From concept to launch and beyond, we cover every layer of your digital stack.</p>
          </div>
          <div className="services-grid">
            {services.map((svc, i) => (
              <div key={svc.title} className={`card service-card animate-fade-up delay-${(i % 3) + 1}`}>
                <div className="icon-box">{svc.icon}</div>
                <h3>{svc.title}</h3>
                <p>{svc.desc}</p>
                <ul className="service-capabilities">
                  {svc.caps.map(c => <li key={c}>{c}</li>)}
                </ul>
                <Link to="/services" className="btn btn-ghost" style={{padding:'0', color:'var(--color-primary-light)', fontWeight:600, fontSize:'0.875rem', display:'inline-flex', alignItems:'center', gap:'0.375rem', background:'none'}}>
                  Learn more <ArrowRight size={14} />
                </Link>
              </div>
            ))}
          </div>
          <div style={{textAlign:'center', marginTop:'var(--space-2xl)'}}>
            <Link to="/services" className="btn btn-primary btn-lg">
              View All Services <ArrowRight size={17} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── WHY ANTI-MATRIX ─────────────────────────── */}
      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container">
          <div className="section-header centered">
            <div className="badge"><Star size={11} /> Why Choose Us</div>
            <h2 style={{color:'var(--color-white)'}}>Built differently. Built better.</h2>
            <div className="divider center"></div>
            <p>We combine the speed of an agency with the depth of an in-house product team.</p>
          </div>
          <div className="grid-4">
            {whyUs.map((w, i) => (
              <div key={w.title} className={`card animate-fade-up delay-${i + 1}`} style={{textAlign:'center', padding:'var(--space-2xl) var(--space-xl)'}}>
                <div className="icon-box" style={{margin:'0 auto var(--space-lg)'}}>{w.icon}</div>
                <h3 style={{fontSize:'1.1rem', color:'var(--color-text)', marginBottom:'var(--space-sm)'}}>{w.title}</h3>
                <p style={{fontSize:'0.9rem'}}>{w.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TECHNOLOGIES ────────────────────────────── */}
      <section className="section-sm reveal" style={{background:'var(--color-bg-alt)', borderTop:'1px solid var(--color-border)', borderBottom:'1px solid var(--color-border)'}}>
        <div className="container">
          <div className="section-header centered" style={{marginBottom:'var(--space-2xl)'}}>
            <p style={{fontSize:'0.8125rem', fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--color-text-dim)'}}>Technologies We Work With</p>
          </div>
          <div style={{display:'flex', flexWrap:'wrap', justifyContent:'center', gap:'var(--space-sm)'}}>
            {technologies.map(t => (
              <span key={t} style={{
                padding: '0.5rem 1.125rem',
                border: '1px solid var(--color-border-light)',
                borderRadius: '999px',
                fontSize: '0.875rem',
                fontFamily: 'var(--font-heading)',
                fontWeight: 600,
                color: 'var(--color-text-muted)',
                background: 'rgba(255,255,255,0.03)',
                transition: 'all 0.25s',
                cursor: 'default',
              }}
              onMouseEnter={e => { e.target.style.borderColor='var(--color-primary)'; e.target.style.color='var(--color-primary-light)' }}
              onMouseLeave={e => { e.target.style.borderColor='var(--color-border-light)'; e.target.style.color='var(--color-text-muted)' }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ────────────────────────────── */}
      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container">
          <div className="section-header centered">
            <div className="badge"><Star size={11} /> Client Stories</div>
            <h2 style={{color:'var(--color-white)'}}>Trusted by innovative companies</h2>
            <div className="divider center"></div>
            <p>Real results, real testimonials from the teams we've had the privilege to work with.</p>
          </div>
          <div className="grid-3">
            {testimonials.map((t, i) => (
              <div key={t.company} className={`testimonial-card animate-fade-up delay-${i + 1}`}>
                <div className="testimonial-stars">
                  {Array.from({length: t.stars}).map((_, j) => <Star key={j} size={14} fill="#f59e0b" />)}
                </div>
                <p className="testimonial-text">"{t.text}"</p>
                <div className="testimonial-author">
                  <div className="testimonial-avatar">{t.initials}</div>
                  <div>
                    <div className="testimonial-company">{t.company}</div>
                    <div className="testimonial-industry">{t.industry}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
