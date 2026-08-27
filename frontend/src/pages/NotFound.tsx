import { Link } from 'react-router-dom'
import { House, ArrowLeft } from '@phosphor-icons/react'

export default function NotFound() {
  return (
    <div className="page-container" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      textAlign: 'center',
    }}>
      <div className="animate-in">
        <div style={{
          fontSize: 72,
          fontWeight: 800,
          fontFamily: 'var(--font-mono)',
          color: 'var(--accent-primary)',
          lineHeight: 1,
          marginBottom: 'var(--space-4)',
          letterSpacing: '-0.04em',
          opacity: 0.6,
        }}>
          404
        </div>
        <h1 style={{
          fontSize: 20,
          fontWeight: 600,
          color: 'var(--text-primary)',
          marginBottom: 'var(--space-3)',
        }}>
          Page not found
        </h1>
        <p style={{
          fontSize: 14,
          color: 'var(--text-secondary)',
          maxWidth: 360,
          lineHeight: 1.6,
          marginBottom: 'var(--space-8)',
        }}>
          The route you requested does not exist. It may have been moved or removed.
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'center' }}>
          <Link to="/" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <House size={14} weight="regular" />
            Dashboard
          </Link>
          <button onClick={() => window.history.back()} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <ArrowLeft size={14} weight="bold" />
            Go Back
          </button>
        </div>
      </div>
    </div>
  )
}
