import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, Activity, Shield, AlertTriangle, Play, ArrowUpRight, Inbox } from 'lucide-react'
import { StatusBadge } from '../components/shared/StatusBadge'
import { formatTime, formatTimestamp, getScoreColor } from '../utils/format'
import type { TestRun } from '../utils/api'

const mockRuns: TestRun[] = [
  { run_id: 'run-a1b2c3d4', timestamp: '2026-08-22T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0abc123', rto_seconds: 152, rpo_seconds: 45, resilience_score: 82, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-e5f6g7h8', timestamp: '2026-08-15T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0def456', rto_seconds: 492, rpo_seconds: 150, resilience_score: 45, status: 'Failed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-i9j0k1l2', timestamp: '2026-08-08T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0ghi789', rto_seconds: 105, rpo_seconds: 30, resilience_score: 91, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-m3n4o5p6', timestamp: '2026-08-01T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0jkl012', rto_seconds: 120, rpo_seconds: 40, resilience_score: 88, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-q7r8s9t0', timestamp: '2026-07-25T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0mno345', rto_seconds: 90, rpo_seconds: 25, resilience_score: 94, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
]

/* ─── Skeleton Loading State ─── */
function DashboardSkeleton() {
  return (
    <div className="page-container">
      <div style={{ marginBottom: 'var(--space-12)' }}>
        <div className="skeleton skeleton-text" style={{ width: 120, height: 24, borderRadius: 9999, marginBottom: 16 }} />
        <div className="skeleton skeleton-heading" />
        <div className="skeleton skeleton-text" style={{ width: '70%' }} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)', marginBottom: 'var(--space-8)' }}>
        <div className="skeleton-card">
          <div className="skeleton skeleton-text" style={{ width: 80, marginBottom: 24 }} />
          <div className="skeleton skeleton-score" style={{ marginBottom: 24 }} />
          <div className="skeleton" style={{ height: 3, borderRadius: 9999 }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton skeleton-metric" />
          ))}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton skeleton-pill" />
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--space-6)' }}>
        <div className="skeleton-card" style={{ height: 240 }} />
        <div className="skeleton-card" style={{ height: 240 }} />
      </div>
    </div>
  )
}

/* ─── Empty State ─── */
function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <Inbox size={28} strokeWidth={1.5} />
      </div>
      <div className="empty-state-title">No test runs yet</div>
      <div className="empty-state-desc">
        Trigger your first disaster recovery test to start measuring system resilience.
      </div>
      <Link to="/new-audit" className="btn btn-primary" style={{ padding: '12px 24px' }}>
        <Play size={14} />
        Run First Test
      </Link>
    </div>
  )
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [runs] = useState<TestRun[]>(mockRuns)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1200)
    return () => clearTimeout(timer)
  }, [])

  if (loading) return <DashboardSkeleton />
  if (runs.length === 0) return <EmptyState />

  const latestRun = runs[0]
  const passRate = Math.round((runs.filter(r => r.status === 'Passed').length / runs.length) * 100)
  const avgScore = Math.round(runs.reduce((sum, r) => sum + r.resilience_score, 0) / runs.length)

  return (
    <div className="page-container">
      {/* Header — asymmetric, left-aligned */}
      <div style={{ marginBottom: 'var(--space-12)' }} className="animate-in">
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '5px 14px',
          background: 'var(--accent-subtle)',
          border: '1px solid rgba(16, 185, 129, 0.15)',
          borderRadius: 9999,
          fontSize: 11,
          fontWeight: 500,
          color: 'var(--accent-primary)',
          marginBottom: 16,
        }}>
          <span className="status-dot status-dot-live" />
          Systems Operational
        </div>
        <h1 style={{
          fontSize: 32,
          fontWeight: 700,
          color: 'var(--text-primary)',
          letterSpacing: '-0.03em',
          lineHeight: 1.1,
          marginBottom: 8,
        }}>
          Resilience Overview
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 15, maxWidth: 480 }}>
          Automated disaster recovery testing. Prove your systems recover when it matters.
        </p>
      </div>

      {/* Hero Score — large, asymmetric */}
      {latestRun && (
        <div className="animate-in animate-in-delay-1" style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--space-6)',
          marginBottom: 'var(--space-8)',
        }}>
          {/* Score card — takes up more space */}
          <div className="card" style={{
            padding: 'var(--space-10)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            position: 'relative',
            overflow: 'hidden',
          }}>
            {/* Ambient glow */}
            <div style={{
              position: 'absolute',
              top: -40,
              right: -40,
              width: 160,
              height: 160,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${getScoreColor(latestRun.resilience_score)}15, transparent 70%)`,
              pointerEvents: 'none',
            }} />

            <div style={{ position: 'relative', zIndex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-8)' }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
                    Latest Run
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-code)' }}>
                    {latestRun.run_id}
                  </div>
                </div>
                <StatusBadge status={latestRun.status} />
              </div>

              {/* Score */}
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 'var(--space-6)' }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 72,
                  fontWeight: 800,
                  color: getScoreColor(latestRun.resilience_score),
                  lineHeight: 1,
                  letterSpacing: '-0.04em',
                }}>
                  {latestRun.resilience_score}
                </span>
                <span style={{ fontSize: 16, color: 'var(--text-muted)', fontWeight: 300 }}>/100</span>
              </div>
            </div>

            {/* Progress bar */}
            <div style={{
              height: 3,
              background: 'rgba(255, 255, 255, 0.04)',
              borderRadius: 9999,
              overflow: 'hidden',
              position: 'relative',
              zIndex: 1,
            }}>
              <div style={{
                height: '100%',
                width: `${latestRun.resilience_score}%`,
                background: `linear-gradient(90deg, ${getScoreColor(latestRun.resilience_score)}, ${getScoreColor(latestRun.resilience_score)}88)`,
                borderRadius: 9999,
                transition: 'width 1.2s cubic-bezier(0.16, 1, 0.3, 1)',
                boxShadow: `0 0 12px ${getScoreColor(latestRun.resilience_score)}40`,
              }} />
            </div>
          </div>

          {/* Metrics column — stacked glass cards with stagger */}
          <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <MetricCard label="RTO" value={formatTime(latestRun.rto_seconds)} target={formatTime(latestRun.rto_target)} ok={latestRun.rto_seconds <= latestRun.rto_target} />
            <MetricCard label="RPO" value={formatTime(latestRun.rpo_seconds)} target={formatTime(latestRun.rpo_target)} ok={latestRun.rpo_seconds <= latestRun.rpo_target} />
            <MetricCard label="Target" value={latestRun.target_resource} target="" ok={true} />
            <MetricCard label="Fault" value={latestRun.fault_type.replace('-', ' ')} target="" ok={true} />
          </div>
        </div>
      )}

      {/* Stats Row — glass pills with stagger */}
      <div className="animate-in animate-in-delay-2" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 'var(--space-4)',
        marginBottom: 'var(--space-8)',
      }}>
        <StatPill icon={<Activity size={16} strokeWidth={1.5} />} label="Total Runs" value={runs.length.toString()} />
        <StatPill icon={<TrendingUp size={16} strokeWidth={1.5} />} label="Pass Rate" value={`${passRate}%`} accent />
        <StatPill icon={<Shield size={16} strokeWidth={1.5} />} label="Avg Score" value={avgScore.toString()} />
        <StatPill icon={<AlertTriangle size={16} strokeWidth={1.5} />} label="Failures" value={runs.filter(r => r.status === 'Failed').length.toString()} danger={runs.filter(r => r.status === 'Failed').length > 0} />
      </div>

      {/* Trend + Recent — asymmetric 2:1 */}
      <div className="animate-in animate-in-delay-3" style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: 'var(--space-6)',
        marginBottom: 'var(--space-8)',
      }}>
        {/* Trend Chart */}
        <div className="card" style={{ padding: 'var(--space-8)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
              Resilience Trend
            </h3>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Last {runs.length} runs
            </span>
          </div>
          <TrendChart runs={runs} />
        </div>

        {/* Recent Runs */}
        <div className="card" style={{ padding: 'var(--space-8)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
              Recent Runs
            </h3>
            <Link to="/runs" style={{
              fontSize: 11,
              color: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}>
              View all <ArrowUpRight size={12} />
            </Link>
          </div>
          <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {runs.slice(0, 4).map((run) => (
              <Link
                key={run.run_id}
                to={`/runs/${run.run_id}`}
                className="stagger-child card-interactive"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid transparent',
                  textDecoration: 'none',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-code)' }}>
                    {run.run_id.slice(0, 12)}
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                    {formatTimestamp(run.timestamp)}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 14,
                    fontWeight: 700,
                    color: getScoreColor(run.resilience_score),
                  }}>
                    {run.resilience_score}
                  </span>
                  <StatusBadge status={run.status} size="sm" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Actions — floating */}
      <div className="animate-in animate-in-delay-4" style={{ display: 'flex', gap: 'var(--space-3)' }}>
        <Link to="/new-audit" className="btn btn-primary" style={{ padding: '12px 24px' }}>
          <Play size={14} />
          Run New Test
        </Link>
        <Link to="/compare" className="btn btn-secondary" style={{ padding: '12px 24px' }}>
          Compare Runs
        </Link>
      </div>
    </div>
  )
}

/* ─── Metric Card (Glass) ─── */
function MetricCard({ label, value, target, ok }: { label: string; value: string; target: string; ok: boolean }) {
  return (
    <div className="stagger-child card-interactive" style={{
      padding: '14px 18px',
      background: 'var(--bg-glass)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      border: '1px solid var(--border-glass)',
      borderRadius: 'var(--radius-lg)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}>
      <div>
        <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 2 }}>
          {label}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
          {value}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {target && (
          <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {target}
          </span>
        )}
        <span style={{
          width: 20,
          height: 20,
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

/* ─── Stat Pill ─── */
function StatPill({ icon, label, value, accent, danger }: { icon: React.ReactNode; label: string; value: string; accent?: boolean; danger?: boolean }) {
  return (
    <div className="card-interactive" style={{
      padding: '16px 18px',
      background: 'var(--bg-glass)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      border: `1px solid ${danger ? 'rgba(244, 63, 94, 0.15)' : 'var(--border-glass)'}`,
      borderRadius: 'var(--radius-lg)',
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
          fontSize: 18,
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

/* ─── Trend Chart ─── */
function TrendChart({ runs }: { runs: TestRun[] }) {
  const reversed = [...runs].reverse()
  const maxScore = 100
  const width = 100
  const height = 40
  const padding = { top: 5, right: 5, bottom: 5, left: 5 }

  const points = reversed.map((run, i) => {
    const x = padding.left + (i / Math.max(reversed.length - 1, 1)) * (width - padding.left - padding.right)
    const y = padding.top + (1 - run.resilience_score / maxScore) * (height - padding.top - padding.bottom)
    return { x, y, run }
  })

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

  // Gradient fill path
  const fillD = pathD + ` L ${points[points.length - 1].x} ${height - padding.bottom} L ${points[0].x} ${height - padding.bottom} Z`

  return (
    <div style={{ position: 'relative' }}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 140 }}>
        <defs>
          <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="var(--accent-primary)" stopOpacity="1" />
          </linearGradient>
          <linearGradient id="fillGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.12" />
            <stop offset="100%" stopColor="var(--accent-primary)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(val => {
          const y = padding.top + (1 - val / maxScore) * (height - padding.top - padding.bottom)
          return (
            <g key={val}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="rgba(255,255,255,0.03)" strokeWidth="0.2" />
              <text x={padding.left - 1.5} y={y + 0.8} fill="var(--text-muted)" fontSize="2.2" fontFamily="var(--font-mono)" textAnchor="end">{val}</text>
            </g>
          )
        })}

        {/* Fill area */}
        <path d={fillD} fill="url(#fillGrad)" />

        {/* Line */}
        <path d={pathD} fill="none" stroke="url(#lineGrad)" strokeWidth="0.7" strokeLinecap="round" strokeLinejoin="round" />

        {/* Dots with glow */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="2" fill="var(--accent-primary)" opacity="0.2" />
            <circle cx={p.x} cy={p.y} r="1.2" fill="var(--accent-primary)" />
          </g>
        ))}
      </svg>

      {/* Labels */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
        {reversed.map((run, i) => (
          <span key={i} style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            {new Date(run.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        ))}
      </div>
    </div>
  )
}
