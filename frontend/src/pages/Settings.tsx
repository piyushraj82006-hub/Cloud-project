import { useState, useEffect } from 'react'
import { Clock } from '@phosphor-icons/react'
import { ThresholdForm } from '../components/Settings/ThresholdForm'
import { AlertConfig } from '../components/Settings/AlertConfig'
import { AccentColorPicker } from '../components/Settings/AccentColorPicker'
import { AlertHistory } from '../components/Settings/AlertHistory'
import { Skeleton } from '../components/shared/Skeleton'

/* ─── Skeleton Loading ─── */
function SettingsSkeleton() {
  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto' }}>
      <Skeleton variant="text" width={80} height={14} borderRadius={4} style={{ marginBottom: 'var(--space-8)' }} />
      <Skeleton variant="card" style={{ marginBottom: 'var(--space-6)' }}>
        <Skeleton variant="text" width={100} height={10} style={{ marginBottom: 20 }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
          {[1, 2, 3].map(i => (
            <div key={i}>
              <Skeleton variant="text" width={80} height={10} style={{ marginBottom: 8 }} />
              <Skeleton variant="pill" height={36} />
            </div>
          ))}
        </div>
        <Skeleton variant="pill" width={120} height={36} />
      </Skeleton>
      <Skeleton variant="card" style={{ marginBottom: 'var(--space-6)' }}>
        <Skeleton variant="text" width={80} height={10} style={{ marginBottom: 20 }} />
        <Skeleton variant="pill" height={36} style={{ marginBottom: 12 }} />
        <Skeleton variant="pill" height={36} />
      </Skeleton>
      <Skeleton variant="card">
        <Skeleton variant="text" width={80} height={10} style={{ marginBottom: 16 }} />
        {[1, 2, 3].map(i => <Skeleton key={i} variant="metric" style={{ marginBottom: i < 3 ? 8 : 0 }} />)}
      </Skeleton>
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
    { date: 'Aug 15', reason: 'RTO exceeded target (8m 12s > 5m)', severity: 'error' as const },
    { date: 'Aug 01', reason: 'Score below threshold (62 < 70)', severity: 'warning' as const },
    { date: 'Jul 18', reason: 'RPO exceeded target (55s > 60s threshold close)', severity: 'info' as const },
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
      <ThresholdForm
        rtoTarget={rtoTarget}
        rpoTarget={rpoTarget}
        scoreThreshold={scoreThreshold}
        onRtoChange={setRtoTarget}
        onRpoChange={setRpoTarget}
        onScoreChange={setScoreThreshold}
        onSave={() => {}}
      />

      {/* Alerts */}
      <AlertConfig
        alertEmail={alertEmail}
        onEmailChange={setAlertEmail}
        onUpdate={() => {}}
      />

      {/* Brand Color */}
      <AccentColorPicker />

      {/* Schedule */}
      <div className="card animate-in animate-in-delay-3" style={{ marginBottom: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
          <span style={{ color: 'var(--accent-primary)' }}><Clock size={14} weight="regular" /></span>
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
          <Clock size={14} weight="regular" />
          Modify Schedule
        </button>
      </div>

      {/* Alert History */}
      <AlertHistory alerts={alertHistory} />
    </div>
  )
}
