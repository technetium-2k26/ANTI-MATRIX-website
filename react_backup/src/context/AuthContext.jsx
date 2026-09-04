import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return localStorage.getItem('antimatrix_logged_in') === 'true'
  })

  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('antimatrix_user')
    return saved ? JSON.parse(saved) : null
  })

  const login = (userData = { name: 'Demo User', email: 'user@anti-matrix.com' }) => {
    setIsLoggedIn(true)
    setUser(userData)
    localStorage.setItem('antimatrix_logged_in', 'true')
    localStorage.setItem('antimatrix_user', JSON.stringify(userData))
  }

  const logout = () => {
    setIsLoggedIn(false)
    setUser(null)
    localStorage.removeItem('antimatrix_logged_in')
    localStorage.removeItem('antimatrix_user')
  }

  return (
    <AuthContext.Provider value={{ isLoggedIn, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
