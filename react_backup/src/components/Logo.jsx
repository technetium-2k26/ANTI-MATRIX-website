import React from 'react'
import { Link } from 'react-router-dom'
import logoDark from '../assets/logo_dark.png'
import logoLight from '../assets/logo_transparent.png'

/*
  Logo component rendering the exact cropped image asset uploaded by the user:
  - logoDark: white/transparent logo (no tagline) for dark backgrounds
  - logoLight: dark/transparent logo (no tagline) for light backgrounds
*/

export default function Logo({ light = true, size = 'md', to = '/' }) {
  const logoSrc = light ? logoDark : logoLight

  // Dimension presets for the tagline-free logo asset
  const heights = {
    sm: 40,
    md: 52,
    lg: 72,
    xl: 90,
  }
  const h = heights[size] ?? heights.md

  const content = (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        userSelect: 'none',
      }}
    >
      <img
        src={logoSrc}
        alt="Anti-Matrix Logo"
        style={{
          height: `${h}px`,
          width: 'auto',
          objectFit: 'contain',
          display: 'block',
        }}
      />
    </div>
  )

  if (to) {
    return (
      <Link to={to} aria-label="Anti-Matrix Home" style={{ textDecoration: 'none', display: 'inline-flex' }}>
        {content}
      </Link>
    )
  }

  return content
}
