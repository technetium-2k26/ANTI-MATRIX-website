/**
 * Anti-Matrix — Navbar & Navigation Controller (Vanilla JS)
 * Exact reproduction of Navbar.jsx scroll & mobile drawer behavior.
 */
document.addEventListener('DOMContentLoaded', () => {
  const navbar = document.getElementById('main-navbar');
  const toggleBtn = document.getElementById('nav-toggle-btn');
  const mobileNav = document.getElementById('mobile-nav');

  if (navbar) {
    // Check scroll on load and on scroll
    const onScroll = () => {
      if (window.scrollY > 30) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  if (toggleBtn && mobileNav) {
    const iconMenu = toggleBtn.querySelector('.icon-menu');
    const iconClose = toggleBtn.querySelector('.icon-close');

    const toggleMenu = (forceState) => {
      const isOpen = typeof forceState === 'boolean' ? forceState : !mobileNav.classList.contains('open');
      if (isOpen) {
        mobileNav.classList.add('open');
        toggleBtn.setAttribute('aria-expanded', 'true');
        mobileNav.setAttribute('aria-hidden', 'false');
        if (iconMenu) iconMenu.style.display = 'none';
        if (iconClose) iconClose.style.display = 'inline-block';
      } else {
        mobileNav.classList.remove('open');
        toggleBtn.setAttribute('aria-expanded', 'false');
        mobileNav.setAttribute('aria-hidden', 'true');
        if (iconMenu) iconMenu.style.display = 'inline-block';
        if (iconClose) iconClose.style.display = 'none';
      }
    };

    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMenu();
    });

    // Close mobile nav when clicking outside
    document.addEventListener('click', (e) => {
      if (mobileNav.classList.contains('open') && !mobileNav.contains(e.target) && !toggleBtn.contains(e.target)) {
        toggleMenu(false);
      }
    });

    // Close mobile nav on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && mobileNav.classList.contains('open')) {
        toggleMenu(false);
      }
    });
  }
});
