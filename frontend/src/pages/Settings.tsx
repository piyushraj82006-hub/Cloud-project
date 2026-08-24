import { useState, useEffect } from 'react'
import { Save, Bell, Clock } from 'lucide-react'

/* ─── Skeleton Loading ─── */
function SettingsSkeleton() {
  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="skeleton skeleton-text" style={{ width: 80, height: 14, borderRadius: 4, marginBottom: 'var(--space-8)' }} />
      <div className="skeleton-card" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="skeleton skeleton-text" style={{ width: 100, height: 10, marginBottom: 20 }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
          {[1, 2, 3].map(i => (
            <div key={i}>
              <div className="skeleton skeleton-text" style={{ width: 80, height: 10, marginBottom: 8 }} />
              <div className="skeleton skeleton-pill" style={{ height: 36 }} />
            </div>
          ))}
        </div>
        <div className="skeleton skeleton-pill" style={{ width: 120, height: 36 }} />
      </div>
      <div className="skeleton-card" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="skeleton skeleton-text" style={{ width: 80, height: 10, marginBottom: 20 }} />
        <div className="skeleton skeleton-pill" style={{ height: 36, marginBottom: 12 }} />
        <div className="skeleton skeleton-pill" style={{ height: 36 }} />
      </div>
      <div className="skeleton-card">
        <div className="skeleton skeleton-text" style={{ width: 80, height: 10, marginBottom: 16 }} />
        {[1, 2, 3].map(i => (
          <div key={i} className="skeleton skeleton-metric" style={{ marginBottom: i < 3 ? 8 : 0 }} />
        ))}
      </div>
    </div>
  )
}

export default function Settings() {
  const [loading, setLoading] = useState(true)
  const [rtoTarget, setRtoTarget] = useState('300')
  const [rpoTarget, setRpoTarget] = useState('60')
  const [scoreThreshold, setScoreThreshold] = useState('70')
  const [alertEmail, setAlertEmail] = useState('admin@example.com')
  const [schedule, setSchedule] = useState('weekly-mon-8am')

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 700)
    return () => clearTimeout(timer)
  }, [])

  const alertHistory = [
    { date: 'Aug 15', reason: 'RTO exceeded target (8m 12s > 5m)', severity: 'error' },
    { date: 'Aug 01', reason: 'Score below threshold (62 < 70)', severity: 'warning' },
    { date: 'Jul 18', reason: 'RPO exceeded target (55s > 60s threshold close)', severity: 'info' },
  ]

  if (loading) return <SettingsSkeleton />

  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-8)' }} className="animate-in">
        <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
          Settings
        </h1>
      </div>

      {/* Thresholds */}
      <div className="card animate-in animate-in-delay-1" style={{ marginBottom: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
          <span style={{ color: 'var(--accent-primary)' }}><Save size={14} /></span>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            THRESHOLDS
          </h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
          <div>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
              RTO TARGET (SECONDS)
            </label>
            <input
              type="number"
              value={rtoTarget}
              onChange={e => setRtoTarget(e.target.value)}
              className="form-input form-input-mono"
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
              RPO TARGET (SECONDS)
            </label>
            <input
              type="number"
              value={rpoTarget}
              onChange={e => setRpoTarget(e.target.value)}
              className="form-input form-input-mono"
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
              SCORE THRESHOLD
            </label>
            <input
              type="number"
              value={scoreThreshold}
              onChange={e => setScoreThreshold(e.target.value)}
              className="form-input form-input-mono"
            />
          </div>
        </div>

        <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Save size={14} />
          Save Changes
        </button>
      </div>

      {/* Alerts */}
      <div className="card animate-in animate-in-delay-2" style={{ marginBottom: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
          <span style={{ color: 'var(--accent-primary)' }}><Bell size={14} /></span>
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
            onChange={e => setAlertEmail(e.target.value)}
            className="form-input"
          />
        </div>

        <button className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Bell size={14} />
          Update Email
        </button>
      </div>

      {/* Schedule */}
      <div className="card animate-in animate-in-delay-3" style={{ marginBottom: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
          <span style={{ color: 'var(--accent-primary)' }}><Clock size={14} /></span>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            SCHEDULE
          </h3>
        </div>

        <select
          value={schedule}
          onChange={e => setSchedule(e.target.value)}
          className="form-input"
          style={{ marginBottom: 'var(--space-4)' }}
        >
          <option value="weekly-mon-8am">Weekly (Monday 08:00 UTC)</option>
          <option value="daily-8am">Daily (08:00 UTC)</option>
          <option value="manual">Manual Only</option>
        </select>

        <button className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Clock size={14} />
          Modify Schedule
        </button>
      </div>

      {/* Alert History */}
      <div className="card animate-in animate-in-delay-4">
        <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
          ALERT HISTORY
        </h3>
        <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {alertHistory.map((alert, i) => (
            <div key={i} className="stagger-child card-interactive" style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              padding: '10px 12px',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-sm)',
            }}>
              <span className={`status-dot ${
                alert.severity === 'error' ? 'status-dot-fail' :
                alert.severity === 'warning' ? '' :
                ''
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
    </div>
  )
}
