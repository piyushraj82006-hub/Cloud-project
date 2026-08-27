import { Bell } from '@phosphor-icons/react'

interface AlertConfigProps {
  alertEmail: string
  onEmailChange: (v: string) => void
  onUpdate: () => void
}

export function AlertConfig({ alertEmail, onEmailChange, onUpdate }: AlertConfigProps) {
  return (
    <div className="card animate-in animate-in-delay-2" style={{ marginBottom: 'var(--space-6)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
        <span style={{ color: 'var(--accent-primary)' }}><Bell size={14} weight="regular" /></span>
        <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
          ALERTS
        </h3>
      </div>

      <div style={{ marginBottom: 'var(--space-4)' }}>
        <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
          SNS TOPIC
        </label>
        <div style={{
          padding: '8px 12px',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-sm)',
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          color: 'var(--text-code)',
        }}>
          cloudguard-dev-alerts
        </div>
      </div>

      <div style={{ marginBottom: 'var(--space-4)' }}>
        <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
          ALERT EMAIL
        </label>
        <input
          type="email"
          value={alertEmail}
          onChange={e => onEmailChange(e.target.value)}
          className="form-input"
        />
      </div>

      <button onClick={onUpdate} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Bell size={14} weight="regular" />
        Update Email
      </button>
    </div>
  )
}
