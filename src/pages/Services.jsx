import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Code2, Smartphone, Brain, TrendingUp, Shield, Globe,
  Server, Palette, ArrowRight, CheckCircle2
} from 'lucide-react'

const services = [
  {
    icon: <Code2 size={28} />,
    title: 'Web Development',
    desc: 'We design and engineer high-performance, scalable web applications that drive business growth and deliver exceptional user experiences across all devices.',
    capabilities: [
      'Custom React / Next.js applications',
      'Full-stack Node.js and Python APIs',
      'E-commerce and marketplace platforms',
      'Progressive Web Apps (PWA)',
      'CMS integrations (Contentful, Sanity)',
      'Performance optimization & Core Web Vitals',
    ],
    tech: ['React', 'Next.js', 'Node.js', 'Python', 'PostgreSQL', 'Redis'],
  },
  {
    icon: <Smartphone size={28} />,
    title: 'Mobile App Development',
    desc: 'From concept to App Store, we build elegant, high-performing mobile applications for iOS and Android using modern cross-platform and native technologies.',
    capabilities: [
      'React Native & Flutter cross-platform apps',
      'Native iOS (Swift) & Android (Kotlin)',
      'App Store & Google Play submission',
      'Offline-first & real-time sync',
      'Push notifications & deep linking',
      'Mobile analytics & crash reporting',
    ],
    tech: ['React Native', 'Flutter', 'Swift', 'Kotlin', 'Firebase'],
  },
  {
    icon: <Brain size={28} />,
    title: 'AI & Machine Learning',
    desc: 'We build intelligent systems that automate processes, extract insights, and create competitive advantages using state-of-the-art AI and machine learning.',
    capabilities: [
      'Predictive analytics & forecasting',
      'Natural Language Processing (NLP)',
      'Computer vision & image recognition',
      'Recommendation engines',
      'LLM integration & fine-tuning',
      'MLOps & model deployment pipelines',
    ],
    tech: ['Python', 'TensorFlow', 'PyTorch', 'OpenAI', 'Hugging Face', 'FastAPI'],
  },
  {
    icon: <TrendingUp size={28} />,
    title: 'Digital Marketing & Growth',
    desc: 'Data-driven marketing strategies that build your brand, attract qualified leads, and convert visitors into loyal, long-term customers.',
    capabilities: [
      'Search Engine Optimization (SEO)',
      'Pay-per-click advertising (Google, Meta)',
      'Social media management & ads',
      'Content strategy & creation',
      'Email marketing automation',
      'Conversion rate optimization (CRO)',
    ],
    tech: ['Google Analytics', 'HubSpot', 'Semrush', 'Mailchimp', 'Meta Ads'],
  },
  {
    icon: <Shield size={28} />,
    title: 'Cloud & DevOps',
    desc: 'Secure, scalable cloud infrastructure with automated pipelines, monitoring, and zero-downtime deployments so your product is always up and fast.',
    capabilities: [
      'AWS, GCP & Azure architecture',
      'Docker & Kubernetes orchestration',
      'CI/CD pipeline automation',
      'Infrastructure as Code (Terraform)',
      'Security audits & penetration testing',
      '24/7 monitoring & incident response',
    ],
    tech: ['AWS', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'GitHub Actions'],
  },
  {
    icon: <Palette size={28} />,
    title: 'UI/UX Design',
    desc: 'Human-centered design that transforms complex problems into intuitive, beautiful digital experiences that users love and keep coming back to.',
    capabilities: [
      'User research & persona development',
      'Information architecture & wireframing',
      'High-fidelity Figma prototypes',
      'Design system creation',
      'Usability testing & iteration',
      'WCAG 2.1 accessibility compliance',
    ],
    tech: ['Figma', 'Adobe XD', 'Maze', 'Hotjar', 'Storybook'],
  },
  {
    icon: <Server size={28} />,
    title: 'Enterprise Software',
    desc: 'Custom enterprise solutions — ERPs, CRMs, internal tools — built to replace legacy systems with modern, scalable, and integrated platforms.',
    capabilities: [
      'Custom ERP & CRM systems',
      'Legacy system modernization',
      'Third-party API integrations',
      'Real-time dashboards & reporting',
      'Role-based access control (RBAC)',
      'Multi-tenant SaaS architecture',
    ],
    tech: ['React', 'Node.js', 'Python', 'PostgreSQL', 'Microservices'],
  },
  {
    icon: <Globe size={28} />,
    title: 'Digital Transformation',
    desc: 'End-to-end digital transformation strategy and execution — helping established businesses evolve their processes, culture, and technology for the digital age.',
    capabilities: [
      'Digital maturity assessment',
      'Technology roadmap planning',
      'Process automation & digitization',
      'Team upskilling & training',
      'Agile transformation coaching',
      'KPI tracking & continuous improvement',
    ],
    tech: ['Strategy', 'Agile', 'JIRA', 'Confluence', 'Miro'],
  },
]

export default function Services() {
  useEffect(() => {
    document.title = 'Services | Anti-Matrix'
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
          <div className="badge"><Code2 size={11} /> Services</div>
          <h1>Everything your digital product needs, under one roof</h1>
          <p>From strategy to execution, we deliver complete technology solutions that help you build, scale, and grow faster.</p>
        </div>
      </section>

      {/* All Services */}
      <section className="section" style={{background:'var(--color-bg)'}}>
        <div className="container">
          <div style={{display:'flex', flexDirection:'column', gap:'var(--space-2xl)'}}>
            {services.map((svc, i) => (
              <div key={svc.title} className="card reveal" style={{
                display:'grid',
                gridTemplateColumns: i % 2 === 0 ? '1fr 1.4fr' : '1.4fr 1fr',
                gap:'var(--space-2xl)',
                alignItems:'center',
                padding:'var(--space-2xl)',
              }}>
                {i % 2 !== 0 && (
                  <div>
                    <div style={{display:'flex', flexWrap:'wrap', gap:'0.5rem', marginBottom:'var(--space-lg)'}}>
                      {svc.tech.map(t => (
                        <span key={t} style={{
                          padding:'0.3rem 0.7rem', borderRadius:'999px',
                          background:'rgba(22,163,74,0.08)', border:'1px solid rgba(22,163,74,0.2)',
                          fontSize:'0.75rem', fontWeight:600, color:'var(--color-primary-light)',
                          fontFamily:'var(--font-heading)'
                        }}>{t}</span>
                      ))}
                    </div>
                    <ul className="service-capabilities">
                      {svc.capabilities.map(c => <li key={c}>{c}</li>)}
                    </ul>
                  </div>
                )}

                <div>
                  <div className="icon-box">{svc.icon}</div>
                  <h3 style={{fontSize:'1.5rem', color:'var(--color-text)', marginBottom:'var(--space-md)'}}>{svc.title}</h3>
                  <p style={{marginBottom:'var(--space-xl)', lineHeight:1.8}}>{svc.desc}</p>
                  <Link to="/contact" className="btn btn-primary">
                    Get Started <ArrowRight size={16} />
                  </Link>
                </div>

                {i % 2 === 0 && (
                  <div>
                    <div style={{display:'flex', flexWrap:'wrap', gap:'0.5rem', marginBottom:'var(--space-lg)'}}>
                      {svc.tech.map(t => (
                        <span key={t} style={{
                          padding:'0.3rem 0.7rem', borderRadius:'999px',
                          background:'rgba(22,163,74,0.08)', border:'1px solid rgba(22,163,74,0.2)',
                          fontSize:'0.75rem', fontWeight:600, color:'var(--color-primary-light)',
                          fontFamily:'var(--font-heading)'
                        }}>{t}</span>
                      ))}
                    </div>
                    <ul className="service-capabilities">
                      {svc.capabilities.map(c => <li key={c}>{c}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Process */}
      <section className="section reveal" style={{background:'var(--color-bg-alt)'}}>
        <div className="container">
          <div className="section-header centered">
            <div className="badge">Our Process</div>
            <h2 style={{color:'var(--color-white)'}}>How we deliver excellence</h2>
            <div className="divider center"></div>
            <p>A proven, structured approach that keeps projects on time, on budget, and on target.</p>
          </div>
          <div className="grid-4">
            {[
              { step:'01', title:'Discovery', desc:'We deeply understand your business goals, users, and technical requirements before writing a single line of code.' },
              { step:'02', title:'Design & Plan', desc:'Architecture blueprints, UI/UX wireframes, and a detailed roadmap agreed upon before development begins.' },
              { step:'03', title:'Build & Iterate', desc:'Agile sprints with weekly demos. You see real progress and can give feedback at every stage.' },
              { step:'04', title:'Launch & Grow', desc:'Rigorous QA, smooth deployment, and ongoing support to continuously optimize and scale your product.' },
            ].map(p => (
              <div key={p.step} className="card" style={{textAlign:'center'}}>
                <div style={{fontFamily:'var(--font-heading)', fontSize:'2.5rem', fontWeight:900, color:'rgba(22,163,74,0.2)', marginBottom:'var(--space-md)'}}>{p.step}</div>
                <h3 style={{fontSize:'1.1rem', color:'var(--color-text)', marginBottom:'var(--space-sm)'}}>{p.title}</h3>
                <p style={{fontSize:'0.875rem'}}>{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section reveal">
        <div className="container">
          <h2>Not sure which service you need?</h2>
          <p>Book a free 30-minute consultation and our experts will recommend the right solution for your business.</p>
          <div className="cta-actions">
            <Link to="/contact" className="btn btn-primary btn-lg">Book Free Consultation <ArrowRight size={17} /></Link>
            <Link to="/pricing" className="btn btn-outline btn-lg">See Pricing</Link>
          </div>
        </div>
      </section>
    </>
  )
}
