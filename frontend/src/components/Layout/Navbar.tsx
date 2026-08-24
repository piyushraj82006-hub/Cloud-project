import { Link, useLocation } from 'react-router-dom'
import { Shield, Activity, GitCompare, Settings, Users } from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Activity },
  { path: '/runs', label: 'Runs', icon: Shield },
  { path: '/compare', label: 'Compare', icon: GitCompare },
  { path: '/clients', label: 'Clients', icon: Users },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export function Navbar() {
  const location = useLocation()

  return (
    <div style={{
      position: 'sticky',
      top: 16,
      zIndex: 100,
      display: 'flex',
      justifyContent: 'center',
      padding: '0 24px',
    }}>
      <nav style={{
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        padding: '6px 8px',
        background: 'rgba(10, 10, 14, 0.8)',
        backdropFilter: 'blur(24px) saturate(1.4)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.4)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: 9999,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.04)',
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
          <span style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: 'var(--accent-primary)',
            boxShadow: '0 0 8px rgba(16, 185, 129, 0.4)',
          }} />
          CG<span style={{ color: 'var(--accent-primary)' }}>DR</span>
        </Link>

        {/* Divider */}
        <div style={{
          width: 1,
          height: 20,
          background: 'rgba(255, 255, 255, 0.06)',
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
                transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.color = 'var(--text-primary)'
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.color = 'var(--text-muted)'
                  e.currentTarget.style.background = 'transparent'
                }
              }}
            >
              <Icon size={14} strokeWidth={1.5} />
              <span style={{ display: 'none' }} className="nav-label-desktop">{item.label}</span>
              <span className="nav-label-desktop">{item.label}</span>
            </Link>
          )
        })}
      </nav>

      <style>{`
        @media (min-width: 768px) {
          .nav-label-desktop { display: inline !important; }
        }
        @media (max-width: 767px) {
          .nav-label-desktop { display: none !important; }
        }
      `}</style>
    </div>
  )
}
