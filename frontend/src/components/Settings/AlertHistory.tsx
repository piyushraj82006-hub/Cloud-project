interface Alert {
  date: string
  reason: string
  severity: 'error' | 'warning' | 'info'
}

interface AlertHistoryProps {
  alerts: Alert[]
}

export function AlertHistory({ alerts }: AlertHistoryProps) {
  return (
    <div className="card animate-in animate-in-delay-4">
      <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
        ALERT HISTORY
      </h3>
      <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {alerts.map((alert, i) => (
          <div key={i} className="stagger-child card-interactive" style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            padding: '10px 12px',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-sm)',
          }}>
            <span className={`status-dot ${
              alert.severity === 'error' ? 'status-dot-fail' : ''
            }`} style={{
              background: alert.severity === 'error' ? 'var(--status-fail)' :
                         alert.severity === 'warning' ? 'var(--status-warn)' :
                         'var(--status-info)',
              width: 6,
              height: 6,
            }} />
            <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', minWidth: 60 }}>
              {alert.date}
            </span>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              {alert.reason}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
