export function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid var(--border-muted)',
      padding: '24px 0',
      marginTop: 'auto',
    }}>
      <div style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '0 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-muted)',
          letterSpacing: '0.08em',
        }}>
          CLOUDGUARD DR — AUTOMATED DISASTER RECOVERY TESTING
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-muted)',
        }}>
          © 2026
        </span>
      </div>
    </footer>
  )
}
