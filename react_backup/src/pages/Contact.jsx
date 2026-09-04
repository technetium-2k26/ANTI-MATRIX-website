import { useEffect, useState } from 'react'
import { Mail, Phone, MapPin, Clock, MessageSquare, Send, CheckCircle2 } from 'lucide-react'

const contactInfo = [
  { icon: <Mail size={20} />,    title: 'Email Us',      value: 'contact@anti-matrix.com', sub: 'We reply within 24 hours' },
  { icon: <Phone size={20} />,   title: 'Call Us',       value: '+1 (555) 000-1234',        sub: 'Mon–Fri, 9am–6pm EST' },
  { icon: <MapPin size={20} />,  title: 'Headquarters',  value: 'San Francisco, CA',        sub: 'United States' },
  { icon: <Clock size={20} />,   title: 'Business Hours', value: 'Mon – Fri, 9am – 6pm',   sub: 'Eastern Standard Time' },
]

const subjects = [
  'New Project Inquiry',
  'Pricing & Packages',
  'Partnership Opportunity',
  'Support & Maintenance',
  'Careers',
  'Other',
]

function validate(form) {
  const errors = {}
  if (!form.name.trim())                     errors.name    = 'Name is required'
  if (!form.email.trim())                    errors.email   = 'Email is required'
  else if (!/\S+@\S+\.\S+/.test(form.email)) errors.email  = 'Enter a valid email address'
  if (!form.subject)                         errors.subject = 'Please select a subject'
  if (!form.message.trim())                  errors.message = 'Message is required'
  else if (form.message.trim().length < 20)  errors.message = 'Message must be at least 20 characters'
  return errors
}

export default function Contact() {
  const [form, setForm]       = useState({ name:'', email:'', phone:'', subject:'', message:'' })
  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    document.title = 'Contact | Anti-Matrix'
    window.scrollTo(0, 0)
    const els = document.querySelectorAll('.reveal')
    const io = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); io.unobserve(e.target) } }),
      { threshold: 0.1 }
    )
    els.forEach(el => io.observe(el))
    return () => io.disconnect()
  }, [])

  const set = k => e => setForm(f => ({...f, [k]: e.target.value}))

  const handleSubmit = async e => {
    e.preventDefault()
    const errs = validate(form)
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    setLoading(true)
    await new Promise(r => setTimeout(r, 1500))
    setLoading(false)
    setSuccess(true)
  }

  return (
    <>
      <section className="page-hero">
        <div className="container">
          <div className="badge"><MessageSquare size={11} /> Contact Us</div>
          <h1>Let's start a conversation</h1>
          <p>Whether you have a project in mind or just want to explore possibilities, our team is ready to help. Reach out — we respond within 24 hours.</p>
        </div>
      </section>

      <section className="section reveal" style={{background:'var(--color-bg)'}}>
        <div className="container">
          <div className="contact-grid">

            {/* Left — contact info */}
            <div>
              <h3 style={{color:'var(--color-white)', marginBottom:'var(--space-sm)'}}>Get in touch</h3>
              <p style={{marginBottom:'var(--space-xl)'}}>
                Fill in the form or reach us directly through any of the channels below. Every inquiry receives a personal response.
              </p>

              {contactInfo.map(c => (
                <div key={c.title} className="contact-info-item">
                  <div className="icon-box" style={{width:'44px', height:'44px', margin:0}}>{c.icon}</div>
                  <div>
                    <h4>{c.title}</h4>
                    <p style={{fontSize:'0.9375rem', fontWeight:500, color:'var(--color-text)'}}>{c.value}</p>
                    <p style={{fontSize:'0.8125rem'}}>{c.sub}</p>
                  </div>
                </div>
              ))}

              <div style={{
                marginTop:'var(--space-xl)', padding:'var(--space-xl)',
                background:'var(--color-primary-glow)', border:'1px solid rgba(34,197,94,0.25)',
                borderRadius:'var(--radius-lg)'
              }}>
                <h4 style={{color:'var(--color-primary-light)', fontFamily:'var(--font-heading)', marginBottom:'var(--space-sm)'}}>
                  Free 30-Minute Consultation
                </h4>
                <p style={{fontSize:'0.9rem', marginBottom:'var(--space-md)'}}>
                  Book a free call with one of our experts to discuss your project requirements and get tailored recommendations.
                </p>
                <div style={{display:'flex', alignItems:'center', gap:'0.5rem'}}>
                  <CheckCircle2 size={15} color="var(--color-primary-light)" />
                  <span style={{fontSize:'0.875rem', color:'var(--color-text-muted)'}}>No commitment required</span>
                </div>
                <div style={{display:'flex', alignItems:'center', gap:'0.5rem', marginTop:'0.5rem'}}>
                  <CheckCircle2 size={15} color="var(--color-primary-light)" />
                  <span style={{fontSize:'0.875rem', color:'var(--color-text-muted)'}}>Expert advice tailored to your goals</span>
                </div>
              </div>
            </div>

            {/* Right — form */}
            <div className="card" style={{padding:'var(--space-2xl)'}}>
              {success ? (
                <div style={{textAlign:'center', padding:'var(--space-2xl) 0'}}>
                  <div style={{
                    width:'64px', height:'64px', background:'var(--color-primary-glow)',
                    borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center',
                    margin:'0 auto var(--space-lg)', border:'2px solid rgba(34,197,94,0.4)'
                  }}>
                    <CheckCircle2 size={28} color="var(--color-primary-light)" />
                  </div>
                  <h3 style={{color:'var(--color-white)', marginBottom:'var(--space-md)'}}>Message sent!</h3>
                  <p>Thank you for reaching out. Our team will review your message and reply within 24 hours.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} noValidate aria-label="Contact form">
                  <h3 style={{color:'var(--color-white)', marginBottom:'var(--space-xl)'}}>Send us a message</h3>

                  <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'var(--space-lg)', marginBottom:'var(--space-lg)'}}>
                    <div className="form-group">
                      <label htmlFor="contact-name">Full Name *</label>
                      <input
                        id="contact-name" type="text" className={`form-control${errors.name ? ' error' : ''}`}
                        placeholder="John Smith" value={form.name} onChange={set('name')}
                        aria-required="true" aria-describedby={errors.name ? 'name-err' : undefined}
                      />
                      {errors.name && <span id="name-err" className="form-error">{errors.name}</span>}
                    </div>
                    <div className="form-group">
                      <label htmlFor="contact-email">Email Address *</label>
                      <input
                        id="contact-email" type="email" className={`form-control${errors.email ? ' error' : ''}`}
                        placeholder="john@company.com" value={form.email} onChange={set('email')}
                        aria-required="true" aria-describedby={errors.email ? 'email-err' : undefined}
                      />
                      {errors.email && <span id="email-err" className="form-error">{errors.email}</span>}
                    </div>
                  </div>

                  <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'var(--space-lg)', marginBottom:'var(--space-lg)'}}>
                    <div className="form-group">
                      <label htmlFor="contact-phone">Phone Number</label>
                      <input
                        id="contact-phone" type="tel" className="form-control"
                        placeholder="+1 555 000 0000" value={form.phone} onChange={set('phone')}
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="contact-subject">Subject *</label>
                      <select
                        id="contact-subject"
                        className={`form-control${errors.subject ? ' error' : ''}`}
                        value={form.subject} onChange={set('subject')}
                        aria-required="true"
                        style={{cursor:'pointer'}}
                      >
                        <option value="">Select a subject...</option>
                        {subjects.map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                      {errors.subject && <span className="form-error">{errors.subject}</span>}
                    </div>
                  </div>

                  <div className="form-group" style={{marginBottom:'var(--space-xl)'}}>
                    <label htmlFor="contact-message">Message *</label>
                    <textarea
                      id="contact-message"
                      className={`form-control${errors.message ? ' error' : ''}`}
                      placeholder="Tell us about your project, goals, timeline, and any specific requirements..."
                      value={form.message} onChange={set('message')}
                      rows={6} aria-required="true"
                    />
                    {errors.message && <span className="form-error">{errors.message}</span>}
                  </div>

                  <button type="submit" className="btn btn-primary w-full" style={{justifyContent:'center'}} disabled={loading}>
                    {loading ? (
                      <>Sending…</>
                    ) : (
                      <><Send size={16} /> Send Message</>
                    )}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
