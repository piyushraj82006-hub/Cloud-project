export function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid var(--border-muted)',
      padding: '24px 0',
      marginTop: 'auto',
    }}>
      <div style={{
        maxWidth: 1400,
        margin: '0 auto',
        padding: '0 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 12,
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-muted)',
          letterSpacing: '0.06em',
        }}>
          CloudGuard DR - Automated Disaster Recovery Testing
        </span>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          fontSize: 11,
          color: 'var(--text-muted)',
        }}>
          <a
            href="#"
            onClick={e => e.preventDefault()}
            style={{ color: 'var(--text-muted)', transition: 'color 150ms ease' }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-primary)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
          >
            Privacy
          </a>
          <a
            href="#"
            onClick={e => e.preventDefault()}
            style={{ color: 'var(--text-muted)', transition: 'color 150ms ease' }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-primary)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
          >
            Terms
          </a>
          <span style={{ fontFamily: 'var(--font-mono)' }}>2026</span>
        </div>
      </div>
    </footer>
  )
}
