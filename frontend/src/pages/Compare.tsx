import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { StatusBadge } from '../components/shared/StatusBadge'
import { formatTime, getScoreColor } from '../utils/format'
import type { TestRun } from '../utils/api'

const mockRuns: TestRun[] = [
  { run_id: 'run-a1b2c3d4', timestamp: '2026-08-22T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0abc123', rto_seconds: 152, rpo_seconds: 45, resilience_score: 82, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-e5f6g7h8', timestamp: '2026-08-15T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0def456', rto_seconds: 492, rpo_seconds: 150, resilience_score: 45, status: 'Failed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-i9j0k1l2', timestamp: '2026-08-08T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0ghi789', rto_seconds: 105, rpo_seconds: 30, resilience_score: 91, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
  { run_id: 'run-m3n4o5p6', timestamp: '2026-08-01T08:00:00Z', fault_type: 'ec2-termination', target_resource: 'i-0jkl012', rto_seconds: 120, rpo_seconds: 40, resilience_score: 88, status: 'Passed', rto_target: 300, rpo_target: 60, report_s3_key: '' },
]

/* ─── Skeleton Loading ─── */
function CompareSkeleton() {
  return (
    <div className="page-container">
      <div className="skeleton skeleton-text" style={{ width: 120, height: 14, borderRadius: 4, marginBottom: 'var(--space-6)' }} />
      <div style={{ display: 'flex', gap: 'var(--space-4)', marginBottom: 'var(--space-6)', alignItems: 'center' }}>
        <div className="skeleton skeleton-pill" style={{ flex: 1, height: 36 }} />
        <div className="skeleton skeleton-text" style={{ width: 20, height: 14 }} />
        <div className="skeleton skeleton-pill" style={{ flex: 1, height: 36 }} />
      </div>
      <div className="skeleton-card" style={{ padding: 0 }}>
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="skeleton" style={{ height: 48, borderBottom: i < 6 ? '1px solid var(--border-primary)' : 'none' }} />
        ))}
      </div>
    </div>
  )
}

export default function Compare() {
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(true)
  const [runA, setRunA] = useState<string>(searchParams.get('a') || mockRuns[0].run_id)
  const [runB, setRunB] = useState<string>(searchParams.get('b') || mockRuns[1].run_id)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 700)
    return () => clearTimeout(timer)
  }, [])

  const selectedA = mockRuns.find(r => r.run_id === runA) || mockRuns[0]
  const selectedB = mockRuns.find(r => r.run_id === runB) || mockRuns[1]

  // Calculate deltas
  const scoreDelta = selectedB.resilience_score - selectedA.resilience_score
  const rtoDelta = selectedB.rto_seconds - selectedA.rto_seconds
  const rpoDelta = selectedB.rpo_seconds - selectedA.rpo_seconds

  if (loading) return <CompareSkeleton />

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-6)' }} className="animate-in">
        <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
          Compare Runs
        </h1>
      </div>

      {/* Selectors */}
      <div style={{ display: 'flex', gap: 'var(--space-4)', marginBottom: 'var(--space-6)', alignItems: 'center' }} className="animate-in animate-in-delay-1">
        <select
          value={runA}
          onChange={e => setRunA(e.target.value)}
          className="select-input"
          style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: 13 }}
        >
          {mockRuns.map(r => (
            <option key={r.run_id} value={r.run_id}>{r.run_id} — {r.status}</option>
          ))}
        </select>

        <span style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 500 }}>vs</span>

        <select
          value={runB}
          onChange={e => setRunB(e.target.value)}
          className="select-input"
          style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: 13 }}
        >
          {mockRuns.map(r => (
            <option key={r.run_id} value={r.run_id}>{r.run_id} — {r.status}</option>
          ))}
        </select>
      </div>

      {/* Comparison Table */}
      <div className="card animate-in animate-in-delay-2" style={{ padding: 0, overflow: 'hidden', marginBottom: 'var(--space-6)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{
                textAlign: 'left',
                fontSize: 10,
                fontWeight: 500,
                color: 'var(--text-muted)',
                letterSpacing: '0.1em',
                padding: '12px 16px',
                borderBottom: '1px solid var(--border-primary)',
                width: '25%',
              }}>
                METRIC
              </th>
              <th style={{
                textAlign: 'left',
                fontSize: 10,
                fontWeight: 500,
                color: 'var(--text-muted)',
                letterSpacing: '0.1em',
                padding: '12px 16px',
                borderBottom: '1px solid var(--border-primary)',
              }}>
                <div style={{ fontFamily: 'var(--font-mono)' }}>{selectedA.run_id}</div>
              </th>
              <th style={{
                textAlign: 'left',
                fontSize: 10,
                fontWeight: 500,
                color: 'var(--text-muted)',
                letterSpacing: '0.1em',
                padding: '12px 16px',
                borderBottom: '1px solid var(--border-primary)',
              }}>
                <div style={{ fontFamily: 'var(--font-mono)' }}>{selectedB.run_id}</div>
              </th>
              <th style={{
                textAlign: 'right',
                fontSize: 10,
                fontWeight: 500,
                color: 'var(--text-muted)',
                letterSpacing: '0.1em',
                padding: '12px 16px',
                borderBottom: '1px solid var(--border-primary)',
              }}>
                DELTA
              </th>
            </tr>
          </thead>
          <tbody>
            <CompareRow
              label="Score"
              valueA={selectedA.resilience_score.toString()}
              valueB={selectedB.resilience_score.toString()}
              delta={scoreDelta}
              inverse={false}
              renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 600, color: getScoreColor(parseInt(v)) }}>{v}</span>}
            />
            <CompareRow
              label="RTO"
              valueA={formatTime(selectedA.rto_seconds)}
              valueB={formatTime(selectedB.rto_seconds)}
              delta={rtoDelta}
              inverse={true}
              renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{v}</span>}
            />
            <CompareRow
              label="RPO"
              valueA={formatTime(selectedA.rpo_seconds)}
              valueB={formatTime(selectedB.rpo_seconds)}
              delta={rpoDelta}
              inverse={true}
              renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{v}</span>}
            />
            <CompareRow
              label="Status"
              valueA={selectedA.status}
              valueB={selectedB.status}
              delta={0}
              renderValue={(v) => <StatusBadge status={v} size="sm" />}
            />
            <CompareRow
              label="RTO Target"
              valueA={formatTime(selectedA.rto_target)}
              valueB={formatTime(selectedB.rto_target)}
              delta={0}
              renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-muted)' }}>{v}</span>}
            />
            <CompareRow
              label="RPO Target"
              valueA={formatTime(selectedA.rpo_target)}
              valueB={formatTime(selectedB.rpo_target)}
              delta={0}
              renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-muted)' }}>{v}</span>}
            />
          </tbody>
        </table>
      </div>

      {/* Delta Summary */}
      <div className="card animate-in animate-in-delay-3">
        <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
          DELTA SUMMARY
        </h3>
        <div className="stagger-children" style={{ borderTop: '1px solid var(--border-muted)', paddingTop: 'var(--space-4)' }}>
          <DeltaItem
            text={`Score ${scoreDelta >= 0 ? 'improved' : 'regressed'} by ${Math.abs(scoreDelta)} points`}
            improved={scoreDelta > 0}
          />
          {rtoDelta > 0 && (
            <DeltaItem
              text={`RTO exceeded target by ${formatTime(selectedB.rto_seconds - selectedB.rto_target)}`}
              improved={false}
            />
          )}
          {rpoDelta > 0 && (
            <DeltaItem
              text={`RPO exceeded target by ${formatTime(selectedB.rpo_seconds - selectedB.rpo_target)}`}
              improved={false}
            />
          )}
          {selectedB.status === 'Failed' && selectedA.status === 'Passed' && (
            <DeltaItem
              text="DNS failover is broken"
              improved={false}
            />
          )}
        </div>
      </div>

      <style>{`
        .select-input {
          background: var(--bg-input);
          border: 1px solid var(--border-primary);
          color: var(--text-primary);
          padding: 8px 12px;
          border-radius: var(--radius-sm);
          font-size: 13;
          font-family: var(--font-primary);
          transition: border-color 150ms var(--ease-out-expo);
        }
        .select-input:focus {
          outline: none;
          border-color: var(--accent-primary);
        }
      `}</style>
    </div>
  )
}

function CompareRow({
  label,
  valueA,
  valueB,
  delta,
  inverse = false,
  renderValue,
}: {
  label: string
  valueA: string
  valueB: string
  delta: number
  inverse?: boolean
  renderValue: (v: string) => React.ReactNode
}) {
  const improved = inverse ? delta < 0 : delta > 0
  const degraded = inverse ? delta > 0 : delta < 0

  return (
    <tr className="table-row-interactive">
      <td style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-muted)',
        fontSize: 12,
        fontWeight: 500,
        color: 'var(--text-muted)',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}>
        {label}
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
        {renderValue(valueA)}
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
        {renderValue(valueB)}
      </td>
      <td style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-muted)',
        textAlign: 'right',
      }}>
        {delta !== 0 && (
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: improved ? 'var(--status-pass)' : degraded ? 'var(--status-fail)' : 'var(--text-muted)',
          }}>
            {improved ? '▼' : degraded ? '▲' : ''} {Math.abs(delta)}
          </span>
        )}
      </td>
    </tr>
  )
}

function DeltaItem({ text, improved }: { text: string; improved: boolean }) {
  return (
    <div className="stagger-child" style={{
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '8px 0',
    }}>
      <span className={`status-dot ${improved ? 'status-dot-live' : 'status-dot-fail'}`} />
      <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
        {text}
      </span>
    </div>
  )
}
