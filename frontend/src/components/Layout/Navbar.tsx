import { Link, useLocation } from 'react-router-dom'
import { Shield, Activity, GitCompare, Settings, Users, Sun, Moon } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Activity },
  { path: '/runs', label: 'Runs', icon: Shield },
  { path: '/compare', label: 'Compare', icon: GitCompare },
  { path: '/clients', label: 'Clients', icon: Users },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export function Navbar() {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  return (
    <div style={{
      position: 'sticky',
      top: 16,
      zIndex: 100,
      display: 'flex',
      justifyContent: 'center',
      padding: '0 24px',
    }}>
      <nav className="navbar-glass" style={{
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        padding: '6px 8px',
        borderRadius: 9999,
      }}>
        {/* Logo */}
        <Link to="/" style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          fontWeight: 600,
          color: 'var(--text-primary)',
          textDecoration: 'none',
          letterSpacing: '-0.02em',
          padding: '8px 14px',
          marginRight: 4,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          whiteSpace: 'nowrap',
        }}>
          <span className="status-dot status-dot-live" />
          CG<span style={{ color: 'var(--accent-primary)' }}>DR</span>
        </Link>

        {/* Divider */}
        <div className="navbar-divider" style={{
          width: 1,
          height: 20,
          marginRight: 4,
        }} />

        {/* Nav Items */}
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className="nav-link-item"
              style={{
                fontSize: 12,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'var(--accent-primary)' : 'var(--text-muted)',
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '7px 12px',
                borderRadius: 9999,
                background: isActive ? 'var(--accent-subtle)' : 'transparent',
                transition: 'all 150ms cubic-bezier(0.16, 1, 0.3, 1)',
                whiteSpace: 'nowrap',
              }}
            >
              <Icon size={14} strokeWidth={1.5} />
              <span className="nav-label-desktop">{item.label}</span>
            </Link>
          )
        })}

        {/* Divider */}
        <div className="navbar-divider" style={{
          width: 1,
          height: 20,
          marginLeft: 4,
        }} />

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="theme-toggle"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 32,
            height: 32,
            borderRadius: 9999,
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            transition: 'all 150ms cubic-bezier(0.16, 1, 0.3, 1)',
          }}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun size={14} strokeWidth={1.5} /> : <Moon size={14} strokeWidth={1.5} />}
        </button>
      </nav>

      <style>{`
        @media (min-width: 768px) {
          .nav-label-desktop { display: inline !important; }
        }
        @media (max-width: 767px) {
          .nav-label-desktop { display: none !important; }
        }
        .nav-link-item:hover:not([style*="accent-primary"]) {
          color: var(--text-primary) !important;
          background: rgba(255, 255, 255, 0.04) !important;
        }
        .nav-link-item:active {
          transform: scale(0.96);
          transition-duration: 80ms;
        }
        .theme-toggle:hover {
          color: var(--text-primary) !important;
          background: rgba(255, 255, 255, 0.04) !important;
        }
        .theme-toggle:active {
          transform: scale(0.9) rotate(15deg);
          transition-duration: 100ms;
        }
      `}</style>
    </div>
  )
}
