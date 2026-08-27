interface Stage {
  name: string
  timestamp: string
}

interface StageTimelineProps {
  stages: Stage[]
}

export function StageTimeline({ stages }: StageTimelineProps) {
  return (
    <div className="card animate-in animate-in-delay-2" style={{ marginBottom: 'var(--space-6)' }}>
      <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-5)' }}>
        STAGE TIMELINE
      </h3>
      <div style={{ display: 'flex', gap: 0, position: 'relative' }}>
        {/* Progress line */}
        <div style={{
          position: 'absolute',
          top: 12,
          left: 24,
          right: 24,
          height: 2,
          background: 'var(--status-pass)',
        }} />

        {stages.map((stage) => (
          <div key={stage.name} style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative',
            zIndex: 1,
          }}>
            {/* Dot */}
            <div style={{
              width: 24,
              height: 24,
              borderRadius: '50%',
              background: 'var(--status-pass)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 8,
            }}>
              <div style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: 'var(--bg-card)',
              }} />
            </div>

            {/* Label */}
            <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>
              {stage.name}
            </span>

            {/* Timestamp */}
            <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              {stage.timestamp}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
