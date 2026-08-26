import { useEffect } from 'react'
import { Link } from 'react-router-dom'

export default function Terms() {
  useEffect(() => {
    document.title = 'Terms of Service | Anti-Matrix'
    window.scrollTo(0, 0)
  }, [])

  return (
    <>
      <section className="page-hero">
        <div className="container">
          <h1>Terms of Service</h1>
          <p>Last updated: January 1, 2026</p>
        </div>
      </section>
      <section className="section" style={{background:'var(--color-bg)'}}>
        <div className="container" style={{maxWidth:'820px', margin:'0 auto'}}>
          {[
            {
              title: '1. Acceptance of Terms',
              content: `By accessing or using Anti-Matrix services, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.`
            },
            {
              title: '2. Services Description',
              content: `Anti-Matrix provides technology consulting, software development, mobile application development, AI/ML systems, digital marketing, and related professional services as described on our website and in individual project agreements.`
            },
            {
              title: '3. Client Responsibilities',
              content: `Clients are responsible for providing accurate project requirements, timely feedback during development, access to necessary systems and credentials, and payment according to agreed schedules.`
            },
            {
              title: '4. Intellectual Property',
              content: `Upon full payment, clients receive full ownership of all custom code, designs, and deliverables created specifically for their project. Anti-Matrix retains rights to our proprietary frameworks, libraries, and methodologies.`
            },
            {
              title: '5. Confidentiality',
              content: `Both parties agree to maintain confidentiality of proprietary information shared during the engagement. Anti-Matrix will sign NDAs upon request before commencing any project discussion.`
            },
            {
              title: '6. Payment Terms',
              content: `Payment schedules are defined in individual project agreements. Standard terms are 30% upfront, 40% at mid-project milestone, and 30% upon delivery. Late payments may incur charges of 1.5% per month.`
            },
            {
              title: '7. Limitation of Liability',
              content: `Anti-Matrix's total liability shall not exceed the total fees paid for the specific project giving rise to the claim. We are not liable for indirect, incidental, or consequential damages.`
            },
            {
              title: '8. Governing Law',
              content: `These terms are governed by the laws of the State of California, United States. Disputes shall be resolved through binding arbitration in San Francisco, California.`
            },
          ].map(s => (
            <div key={s.title} style={{marginBottom:'var(--space-2xl)'}}>
              <h3 style={{color:'var(--color-white)', marginBottom:'var(--space-md)'}}>{s.title}</h3>
              <p>{s.content}</p>
            </div>
          ))}
          <div style={{marginTop:'var(--space-2xl)'}}>
            <Link to="/contact" className="btn btn-outline">Contact Us With Questions</Link>
          </div>
        </div>
      </section>
    </>
  )
}
