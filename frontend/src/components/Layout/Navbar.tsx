import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Pulse, ShieldCheck, GitDiff, GearSix, Users, Sun, Moon, List, X } from '@phosphor-icons/react'
import { useTheme } from '../../contexts/ThemeContext'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Pulse },
  { path: '/runs', label: 'Runs', icon: ShieldCheck },
  { path: '/compare', label: 'Compare', icon: GitDiff },
  { path: '/clients', label: 'Clients', icon: Users },
  { path: '/settings', label: 'Settings', icon: GearSix },
]

export function Navbar() {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <>
      <div style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        borderBottom: '1px solid var(--border-primary)',
        background: 'var(--bg-primary)',
      }}>
        <nav style={{
          display: 'flex',
          alignItems: 'center',
          maxWidth: 1400,
          margin: '0 auto',
          padding: '0 32px',
          height: 56,
          gap: 4,
        }}>
          {/* Logo */}
          <Link to="/" style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            fontWeight: 600,
            color: 'var(--text-primary)',
            textDecoration: 'none',
            letterSpacing: '-0.02em',
            marginRight: 32,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            whiteSpace: 'nowrap',
          }}>
            <span className="status-dot status-dot-live" />
            CG<span style={{ color: 'var(--accent-primary)' }}>DR</span>
          </Link>

          {/* Nav Items - Desktop */}
          <div className="nav-desktop-only" style={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    fontSize: 13,
                    fontWeight: isActive ? 500 : 400,
                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: isActive ? 'var(--bg-hover)' : 'transparent',
                    transition: 'all 150ms ease',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <Icon size={14} weight={isActive ? 'fill' : 'regular'} />
                  {item.label}
                </Link>
              )
            })}
          </div>

          {/* Spacer */}
          <div style={{ flex: 1 }} className="nav-desktop-only" />

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-sm)',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              transition: 'all 150ms ease',
            }}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <Sun size={14} weight="regular" /> : <Moon size={14} weight="regular" />}
          </button>

          {/* Hamburger - Mobile */}
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="hamburger-btn"
            style={{
              display: 'none',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-sm)',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
            }}
            aria-label="Open navigation menu"
          >
            <List size={16} weight="regular" />
          </button>
        </nav>
      </div>

      {/* Mobile Overlay Menu */}
      {mobileMenuOpen && (
        <div
          onClick={() => setMobileMenuOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 200,
            background: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            animation: 'fadeIn 0.15s ease forwards',
          }}
        >
          <button
            onClick={() => setMobileMenuOpen(false)}
            style={{
              position: 'absolute',
              top: 16,
              right: 16,
              width: 36,
              height: 36,
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid var(--border-primary)',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            aria-label="Close navigation menu"
          >
            <X size={16} />
          </button>

          <div onClick={e => e.stopPropagation()} style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '80%', maxWidth: 280 }}>
            {navItems.map((item, i) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  style={{
                    fontSize: 15,
                    fontWeight: isActive ? 500 : 400,
                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-sm)',
                    background: isActive ? 'var(--bg-hover)' : 'transparent',
                    transition: 'all 150ms ease',
                    animation: `fadeInUp 0.3s ease ${i * 0.05}s forwards`,
                    opacity: 0,
                  }}
                >
                  <Icon size={16} weight={isActive ? 'fill' : 'regular'} />
                  {item.label}
                </Link>
              )
            })}
          </div>
        </div>
      )}

      <style>{`
        @media (min-width: 768px) {
          .nav-desktop-only { display: flex !important; }
          .hamburger-btn { display: none !important; }
        }
        @media (max-width: 767px) {
          .nav-desktop-only { display: none !important; }
          .hamburger-btn { display: flex !important; }
        }
      `}</style>
    </>
  )
}
