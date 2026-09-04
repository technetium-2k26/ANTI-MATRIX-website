import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  MapPin, Clock, ChevronRight, Heart, Zap, Users, Award,
  ArrowRight, Briefcase, Code2, TrendingUp, Brain, Palette
} from 'lucide-react'

const perks = [
  { icon: <Zap size={20} />,     title: 'Remote-First',     desc: 'Work from anywhere in the world. Our team spans 12+ countries — collaboration is in our DNA.' },
  { icon: <Heart size={20} />,   title: 'Health & Wellness', desc: 'Comprehensive health, dental, and vision coverage plus a $500 annual wellness budget.' },
  { icon: <Award size={20} />,   title: 'Growth Budget',     desc: '$1,500/year for courses, conferences, books, and certifications to keep you at the frontier.' },
  { icon: <Users size={20} />,   title: 'Equity Options',    desc: 'Meaningful equity for every full-time team member. When Anti-Matrix wins, you win too.' },
  { icon: <Clock size={20} />,   title: 'Flexible Hours',    desc: 'Async-first culture with flexible scheduling. Outcomes matter more than hours at a desk.' },
  { icon: <Brain size={20} />,   title: 'Cutting-Edge Work', desc: 'Work on AI, cloud infrastructure, and modern web products — always on the leading edge.' },
]

const openRoles = [
  {
    title: 'Senior Full-Stack Engineer',
    dept: 'Engineering',
    location: 'Remote (Worldwide)',
    type: 'Full-time',
    skills: ['React', 'Node.js', 'PostgreSQL', 'AWS'],
    desc: 'We are looking for a senior full-stack engineer to lead the development of complex web applications for our enterprise clients. You will work closely with product, design, and client teams.',
    reqs: ['5+ years of full-stack experience', 'Strong React and Node.js expertise', 'Experience with cloud services (AWS/GCP)', 'Excellent communication skills'],
  },
  {
    title: 'Machine Learning Engineer',
    dept: 'AI & Data',
    location: 'Remote (US/EU)',
    type: 'Full-time',
    skills: ['Python', 'PyTorch', 'MLOps', 'FastAPI'],
    desc: 'Join our AI team to design and deploy production machine learning systems. You will work on NLP, computer vision, and predictive analytics projects for our clients.',
    reqs: ['3+ years ML engineering experience', 'Proficiency in Python and PyTorch/TensorFlow', 'Experience with model deployment & MLOps', 'Background in NLP or computer vision preferred'],
  },
  {
    title: 'UI/UX Designer',
    dept: 'Design',
    location: 'Remote (Worldwide)',
    type: 'Full-time',
    skills: ['Figma', 'User Research', 'Prototyping', 'Design Systems'],
    desc: 'We need a talented UI/UX designer to craft intuitive, beautiful experiences for our web and mobile products. You will own design from research and wireframing through to high-fidelity delivery.',
    reqs: ['3+ years UI/UX design experience', 'Expert-level Figma skills', 'Strong portfolio of shipped products', 'Experience with design systems'],
  },
  {
    title: 'React Native Developer',
    dept: 'Mobile',
    location: 'Remote (Worldwide)',
    type: 'Full-time',
    skills: ['React Native', 'TypeScript', 'iOS', 'Android'],
    desc: 'Build high-performance, cross-platform mobile applications for iOS and Android. You will work on projects ranging from consumer apps to enterprise mobile solutions.',
    reqs: ['3+ years React Native experience', 'Published apps on App Store / Google Play', 'Strong TypeScript skills', 'Familiarity with native iOS or Android development'],
  },
  {
    title: 'DevOps / Cloud Engineer',
    dept: 'Infrastructure',
    location: 'Remote (US/EU)',
    type: 'Full-time',
    skills: ['AWS', 'Kubernetes', 'Terraform', 'CI/CD'],
    desc: 'Design and manage the cloud infrastructure that powers our clients\' digital products. You will build automated pipelines, ensure security and reliability, and reduce operational overhead.',
    reqs: ['4+ years DevOps/SRE experience', 'AWS or GCP certification preferred', 'Kubernetes and Terraform experience', 'Strong security mindset'],
  },
  {
    title: 'Digital Marketing Specialist',
    dept: 'Marketing',
    location: 'Remote (Worldwide)',
    type: 'Full-time',
    skills: ['SEO', 'Google Ads', 'Analytics', 'Content Strategy'],
    desc: 'Drive measurable growth for Anti-Matrix clients through data-backed digital marketing strategies. You will manage campaigns, optimize performance, and report on ROI.',
    reqs: ['3+ years digital marketing experience', 'Google Ads and Meta Ads certified', 'Strong analytical skills (GA4, Looker)', 'Excellent English writing skills'],
  },
]

export default function Careers() {
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    document.title = 'Careers | Anti-Matrix'
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
          <div className="badge"><Briefcase size={11} /> Join the Team</div>
          <h1>Build remarkable technology.<br />Do the best work of your life.</h1>
          <p>Anti-Matrix is a team of engineers, designers, and strategists solving real problems for real businesses. We're growing fast — come grow with us.</p>
        </div>
      </section>

      {/* Why Work Here */}
      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container">
          <div className="section-header centered">
            <div className="badge"><Heart size={11} /> Life at Anti-Matrix</div>
            <h2 style={{color:'var(--color-white)'}}>Why people love working here</h2>
            <div className="divider center"></div>
            <p>We've built a culture where great people can do their best work — with autonomy, support, and real impact.</p>
          </div>
          <div className="grid-3">
            {perks.map(p => (
              <div key={p.title} className="card" style={{textAlign:'center'}}>
                <div className="icon-box" style={{margin:'0 auto var(--space-lg)'}}>{p.icon}</div>
                <h3 style={{fontSize:'1.05rem', color:'var(--color-text)', marginBottom:'var(--space-sm)'}}>{p.title}</h3>
                <p style={{fontSize:'0.9rem'}}>{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Open Roles */}
      <section className="section reveal" style={{background:'var(--color-bg-alt)'}}>
        <div className="container">
          <div className="section-header">
            <div className="badge"><Briefcase size={11} /> Open Positions</div>
            <h2 style={{color:'var(--color-white)'}}>Current openings</h2>
            <div className="divider"></div>
            <p>All roles are fully remote. We welcome applications from anywhere in the world.</p>
          </div>

          <div style={{display:'flex', flexDirection:'column', gap:'var(--space-md)'}}>
            {openRoles.map((role, i) => (
              <div key={role.title}>
                <div
                  className="card job-card"
                  style={{cursor:'pointer', borderColor: selected === i ? 'rgba(22,163,74,0.35)' : ''}}
                  onClick={() => setSelected(selected === i ? null : i)}
                >
                  <div className="job-info">
                    <div className="job-title">{role.title}</div>
                    <div className="job-meta">
                      <span className="job-tag dept">{role.dept}</span>
                      <span className="job-tag loc"><MapPin size={11} /> {role.location}</span>
                      <span className="job-tag loc"><Clock size={11} /> {role.type}</span>
                    </div>
                    <div className="job-skills">
                      {role.skills.map(s => <span key={s} className="skill-tag">{s}</span>)}
                    </div>
                  </div>
                  <div className="job-actions">
                    <span className="btn btn-outline btn-sm">
                      {selected === i ? 'Collapse' : 'View Role'} <ChevronRight size={15} style={{transform: selected === i ? 'rotate(90deg)' : 'none', transition:'transform 0.2s'}} />
                    </span>
                  </div>
                </div>

                {/* Expanded job details */}
                {selected === i && (
                  <div className="card animate-fade-up" style={{marginTop:'var(--space-sm)', borderColor:'rgba(22,163,74,0.2)', background:'rgba(22,163,74,0.03)'}}>
                    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'var(--space-xl)'}}>
                      <div>
                        <h4 style={{color:'var(--color-text)', marginBottom:'var(--space-md)', fontFamily:'var(--font-heading)'}}>About the Role</h4>
                        <p style={{marginBottom:'var(--space-lg)'}}>{role.desc}</p>
                        <h4 style={{color:'var(--color-text)', marginBottom:'var(--space-md)', fontFamily:'var(--font-heading)'}}>Requirements</h4>
                        <ul className="service-capabilities">
                          {role.reqs.map(r => <li key={r}>{r}</li>)}
                        </ul>
                      </div>
                      <div style={{display:'flex', flexDirection:'column', justifyContent:'center', alignItems:'flex-start', gap:'var(--space-md)'}}>
                        <div>
                          <div style={{fontSize:'0.8rem', color:'var(--color-text-dim)', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:700, fontFamily:'var(--font-heading)', marginBottom:'0.375rem'}}>Department</div>
                          <div style={{color:'var(--color-text)'}}>{role.dept}</div>
                        </div>
                        <div>
                          <div style={{fontSize:'0.8rem', color:'var(--color-text-dim)', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:700, fontFamily:'var(--font-heading)', marginBottom:'0.375rem'}}>Location</div>
                          <div style={{color:'var(--color-text)'}}>{role.location}</div>
                        </div>
                        <div>
                          <div style={{fontSize:'0.8rem', color:'var(--color-text-dim)', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:700, fontFamily:'var(--font-heading)', marginBottom:'0.375rem'}}>Type</div>
                          <div style={{color:'var(--color-text)'}}>{role.type}</div>
                        </div>
                        <a
                          href={`mailto:careers@anti-matrix.com?subject=Application: ${role.title}`}
                          className="btn btn-primary"
                          style={{marginTop:'var(--space-md)'}}
                        >
                          Apply Now <ArrowRight size={16} />
                        </a>
                        <p style={{fontSize:'0.8125rem', color:'var(--color-text-dim)'}}>
                          Send your CV and portfolio to <span style={{color:'var(--color-primary-light)'}}>careers@anti-matrix.com</span>
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* General Application */}
      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container" style={{maxWidth:'640px', margin:'0 auto', textAlign:'center'}}>
          <div className="badge" style={{margin:'0 auto var(--space-lg)'}}><Users size={11} /> Don't see your role?</div>
          <h2 style={{color:'var(--color-white)', marginBottom:'var(--space-md)'}}>Send us a general application</h2>
          <p style={{marginBottom:'var(--space-2xl)'}}>
            We're always on the lookout for exceptional talent. If you're passionate about building great technology and don't see your ideal role listed, introduce yourself anyway.
          </p>
          <a
            href="mailto:careers@anti-matrix.com?subject=General Application"
            className="btn btn-primary btn-lg"
          >
            Send Your Application <ArrowRight size={17} />
          </a>
        </div>
      </section>
    </>
  )
}
