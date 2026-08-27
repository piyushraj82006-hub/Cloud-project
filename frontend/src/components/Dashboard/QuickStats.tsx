import { Pulse, TrendUp, ShieldCheck, Warning } from '@phosphor-icons/react'
import type { TestRun } from '../../utils/api'

interface QuickStatsProps {
  runs: TestRun[]
}

function StatPill({ icon, label, value, accent, danger }: { icon: React.ReactNode; label: string; value: string; accent?: boolean; danger?: boolean }) {
  return (
    <div style={{
      padding: '14px 16px',
      background: 'var(--bg-card)',
      border: `1px solid ${danger ? 'rgba(239, 68, 68, 0.15)' : 'var(--border-primary)'}`,
      borderRadius: 'var(--radius-sm)',
      display: 'flex',
      alignItems: 'center',
      gap: 12,
    }}>
      <span style={{ color: accent ? 'var(--accent-primary)' : danger ? 'var(--status-fail)' : 'var(--text-muted)' }}>
        {icon}
      </span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 1 }}>{label}</div>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 17,
          fontWeight: 700,
          color: accent ? 'var(--accent-primary)' : danger ? 'var(--status-fail)' : 'var(--text-primary)',
          letterSpacing: '-0.02em',
        }}>
          {value}
        </div>
      </div>
    </div>
  )
}

export function QuickStats({ runs }: QuickStatsProps) {
  const passRate = Math.round((runs.filter(r => r.status === 'Passed').length / runs.length) * 100)
  const avgScore = Math.round(runs.reduce((sum, r) => sum + r.resilience_score, 0) / runs.length)
  const failures = runs.filter(r => r.status === 'Failed').length

  return (
    <div className="animate-in animate-in-delay-2" style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: 'var(--space-3)',
      marginBottom: 'var(--space-8)',
    }}>
      <StatPill icon={<Pulse size={15} weight="regular" />} label="Total Runs" value={runs.length.toString()} />
      <StatPill icon={<TrendUp size={15} weight="regular" />} label="Pass Rate" value={`${passRate}%`} accent />
      <StatPill icon={<ShieldCheck size={15} weight="regular" />} label="Avg Score" value={avgScore.toString()} />
      <StatPill icon={<Warning size={15} weight="regular" />} label="Failures" value={failures.toString()} danger={failures > 0} />
    </div>
  )
}
