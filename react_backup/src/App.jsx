import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { useEffect } from 'react'

import { AuthProvider } from './context/AuthContext.jsx'
import ProtectedRoute   from './components/ProtectedRoute.jsx'

import Navbar   from './components/Navbar.jsx'
import Footer   from './components/Footer.jsx'

import Home     from './pages/Home.jsx'
import About    from './pages/About.jsx'
import Services from './pages/Services.jsx'
import Pricing  from './pages/Pricing.jsx'
import Careers  from './pages/Careers.jsx'
import Contact  from './pages/Contact.jsx'
import Login    from './pages/Login.jsx'
import Signup   from './pages/Signup.jsx'
import Privacy  from './pages/Privacy.jsx'
import Terms    from './pages/Terms.jsx'
import NotFound from './pages/NotFound.jsx'

/* Pages that show Navbar + Footer */
const AUTH_ROUTES = ['/login', '/signup']

function Layout() {
  const location = useLocation()
  const isAuth   = AUTH_ROUTES.includes(location.pathname)

  // Scroll to top on route change
  useEffect(() => { window.scrollTo(0, 0) }, [location.pathname])

  // Scroll reveal re-init on route change
  useEffect(() => {
    const timer = setTimeout(() => {
      const els = document.querySelectorAll('.reveal:not(.revealed)')
      const io  = new IntersectionObserver(
        entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); io.unobserve(e.target) } }),
        { threshold: 0.1 }
      )
      els.forEach(el => io.observe(el))
      return () => io.disconnect()
    }, 100)
    return () => clearTimeout(timer)
  }, [location.pathname])

  return (
    <>
      {!isAuth && <Navbar />}
      <main id="main-content">
        <Routes>
          <Route path="/"        element={<Home />}     />
          <Route path="/about"   element={<About />}    />
          <Route path="/services" element={<Services />} />
          <Route
            path="/pricing"
            element={
              <ProtectedRoute title="Pricing & Packages">
                <Pricing />
              </ProtectedRoute>
            }
          />
          <Route path="/careers" element={<Careers />}  />
          <Route path="/contact" element={<Contact />}  />
          <Route path="/login"   element={<Login />}    />
          <Route path="/signup"  element={<Signup />}   />
          <Route path="/privacy" element={<Privacy />}  />
          <Route path="/terms"   element={<Terms />}    />
          <Route path="*"        element={<NotFound />} />
        </Routes>
      </main>
      {!isAuth && <Footer />}
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    </AuthProvider>
  )
}
