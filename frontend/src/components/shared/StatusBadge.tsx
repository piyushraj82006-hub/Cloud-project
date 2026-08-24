interface StatusBadgeProps {
  status: string
  size?: 'sm' | 'md'
}

const statusConfig: Record<string, { bg: string; color: string; label: string }> = {
  Passed: { bg: 'var(--status-pass)', color: 'white', label: 'PASSED' },
  Failed: { bg: 'var(--status-fail)', color: 'white', label: 'FAILED' },
  Incomplete: { bg: 'var(--status-warn)', color: 'var(--bg-primary)', label: 'INCOMPLETE' },
  'External Audit': { bg: 'var(--status-info)', color: 'white', label: 'EXTERNAL' },
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status] || { bg: 'var(--text-muted)', color: 'white', label: status.toUpperCase() }
  const fontSize = size === 'sm' ? 10 : 11
  const padding = size === 'sm' ? '2px 6px' : '4px 8px'

  return (
    <span
      role="status"
      aria-label={`Status: ${config.label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding,
        background: config.bg,
        color: config.color,
        fontSize,
        fontWeight: 600,
        fontFamily: 'var(--font-mono)',
        letterSpacing: '0.05em',
        borderRadius: 'var(--radius-sm)',
        textTransform: 'uppercase',
      }}
    >
      <span style={{
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: 'currentColor',
        opacity: 0.8,
      }} />
      {config.label}
    </span>
  )
}
