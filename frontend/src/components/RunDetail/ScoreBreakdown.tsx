import { formatTime, getScoreColor } from '../../utils/format'
import type { TestRun } from '../../utils/api'

interface ScoreBreakdownProps {
  run: TestRun
}

function MetricRow({ label, actual, target, ok }: { label: string; actual: string; target: string; ok: boolean }) {
  return (
    <div className="stagger-child card-interactive" style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '8px 12px',
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius-sm)',
    }}>
      <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
        {label}
      </span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>
          {actual}
        </span>
        {target && (
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            (target: {target})
          </span>
        )}
        <span style={{
          width: 18,
          height: 18,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: ok ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
        }}>
          {ok ? (
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--status-pass)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          ) : (
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--status-fail)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          )}
        </span>
      </div>
    </div>
  )
}

export function ScoreBreakdown({ run }: ScoreBreakdownProps) {
  return (
    <div className="card animate-in animate-in-delay-1" style={{ padding: 'var(--space-8)', marginBottom: 'var(--space-6)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-8)' }}>
        {/* Left: Score */}
        <div>
          <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>
            RESILIENCE SCORE
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 48,
              fontWeight: 700,
              color: getScoreColor(run.resilience_score),
            }}>
              {run.resilience_score}
            </span>
            <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>/100</span>
          </div>
        </div>

        {/* Right: Metrics */}
        <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <MetricRow label="RTO" actual={formatTime(run.rto_seconds)} target={formatTime(run.rto_target)} ok={run.rto_seconds <= run.rto_target} />
          <MetricRow label="RPO" actual={formatTime(run.rpo_seconds)} target={formatTime(run.rpo_target)} ok={run.rpo_seconds <= run.rpo_target} />
          <MetricRow label="TARGET" actual={run.target_resource} target="" ok={true} />
          <MetricRow label="FAULT" actual={run.fault_type} target="" ok={true} />
        </div>
      </div>
    </div>
  )
}
