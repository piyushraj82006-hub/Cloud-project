import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Play, GitCompare, Inbox } from 'lucide-react'
import { StatusBadge } from '../components/shared/StatusBadge'
import { formatTime, formatTimestamp, getScoreColor } from '../utils/format'
import type { TestRun } from '../utils/api'

const mockRuns: TestRun[] = [
  { run_id: 'run-a1b2c3d4', timestamp: '2026-08-22T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0abc123', rto_seconds: 152, rpo_seconds: 45, resilience_score: 82, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-e5f6g7h8', timestamp: '2026-08-15T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0def456', rto_seconds: 492, rpo_seconds: 150, resilience_score: 45, status: 'Failed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-i9j0k1l2', timestamp: '2026-08-08T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0ghi789', rto_seconds: 105, rpo_seconds: 30, resilience_score: 91, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-m3n4o5p6', timestamp: '2026-08-01T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0jkl012', rto_seconds: 120, rpo_seconds: 40, resilience_score: 88, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-q7r8s9t0', timestamp: '2026-07-25T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0mno345', rto_seconds: 90, rpo_seconds: 25, resilience_score: 94, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-u1v2w3x4', timestamp: '2026-07-18T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0pqr678', rto_seconds: 180, rpo_seconds: 55, resilience_score: 78, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
]

/* ─── Skeleton Loading State ─── */
function RunsSkeleton() {
  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
        <div className="skeleton skeleton-text" style={{ width: 80, height: 14, borderRadius: 4 }} />
        <div className="skeleton skeleton-pill" style={{ width: 120, height: 36, borderRadius: 9999 }} />
      </div>
      <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
        <div className="skeleton skeleton-pill" style={{ width: 100, height: 32 }} />
        <div className="skeleton skeleton-pill" style={{ width: 120, height: 32 }} />
      </div>
      <div className="skeleton-card" style={{ padding: 0 }}>
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="skeleton" style={{ height: 52, borderBottom: i < 5 ? '1px solid var(--border-primary)' : 'none' }} />
        ))}
      </div>
    </div>
  )
}

/* ─── Empty State ─── */
function RunsEmpty() {
  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
        <div>
          <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
            Runs
          </h1>
        </div>
        <Link to="/new-audit" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Play size={14} />
          New Test
        </Link>
      </div>
      <div className="empty-state">
        <div className="empty-state-icon">
          <Inbox size={28} strokeWidth={1.5} />
        </div>
        <div className="empty-state-title">No test runs found</div>
        <div className="empty-state-desc">
          Adjust your filters or run a new disaster recovery test to see results here.
        </div>
      </div>
    </div>
  )
}

export default function Runs() {
  const [loading, setLoading] = useState(true)
  const [runs] = useState<TestRun[]>(mockRuns)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [faultFilter, setFaultFilter] = useState<string>('')

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800)
    return () => clearTimeout(timer)
  }, [])

  const filtered = runs.filter(r => {
    if (statusFilter && r.status !== statusFilter) return false
    if (faultFilter && r.fault_type !== faultFilter) return false
    return true
  })

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else if (next.size < 2) next.add(id)
      return next
    })
  }

  if (loading) return <RunsSkeleton />
  if (runs.length === 0) return <RunsEmpty />

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
        <div>
          <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
            Runs
          </h1>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          {selected.size === 2 && (
            <Link to={`/compare?a=${Array.from(selected)[0]}&b=${Array.from(selected)[1]}`} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <GitCompare size={14} />
              Compare Selected ({selected.size})
            </Link>
          )}
          <Link to="/new-audit" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Play size={14} />
            New Test
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="select-input"
        >
          <option value="">All Status</option>
          <option value="Passed">Passed</option>
          <option value="Failed">Failed</option>
          <option value="Incomplete">Incomplete</option>
        </select>
        <select
          value={faultFilter}
          onChange={e => setFaultFilter(e.target.value)}
          className="select-input"
        >
          <option value="">All Fault Types</option>
          <option value="ec2-termination">EC2 Termination</option>
        </select>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ width: 40 }}></th>
              {['RUN ID', 'STATUS', 'SCORE', 'RTO', 'RPO', 'DATE'].map(header => (
                <th key={header} style={{
                  textAlign: 'left',
                  fontSize: 10,
                  fontWeight: 500,
                  color: 'var(--text-muted)',
                  letterSpacing: '0.1em',
                  padding: '12px 16px',
                  borderBottom: '1px solid var(--border-primary)',
                }}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((run, i) => (
              <tr
                key={run.run_id}
                className="table-row-interactive stagger-child"
                style={{
                  cursor: 'pointer',
                  background: selected.has(run.run_id) ? 'var(--accent-muted)' : 'transparent',
                  animationDelay: `${i * 0.04}s`,
                }}
              >
                <td style={{ padding: '12px 8px 12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
                  <input
                    type="checkbox"
                    checked={selected.has(run.run_id)}
                    onChange={() => toggleSelect(run.run_id)}
                    style={{ accentColor: 'var(--accent-primary)' }}
                  />
                </td>
                <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
                  <Link to={`/runs/${run.run_id}`} style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-code)' }}>
                    {run.run_id}
                  </Link>
                </td>
                <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
                  <StatusBadge status={run.status} size="sm" />
                </td>
                <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, color: getScoreColor(run.resilience_score) }}>
                    {run.resilience_score}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>
                    {formatTime(run.rto_seconds)}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>
                    {formatTime(run.rpo_seconds)}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {formatTimestamp(run.timestamp)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <style>{`
        .select-input {
          background: var(--bg-input);
          border: 1px solid var(--border-primary);
          color: var(--text-primary);
          padding: 6px 12px;
          border-radius: var(--radius-sm);
          font-size: 12;
          font-family: var(--font-primary);
          transition: border-color 150ms var(--ease-out-expo);
        }
        .select-input:focus {
          outline: none;
          border-color: var(--accent-primary);
        }
        .table-row-interactive {
          transition: background var(--transition-fast);
        }
        .table-row-interactive:hover {
          background: var(--bg-hover) !important;
        }
      `}</style>
    </div>
  )
}
