import { StatusBadge } from '../shared/StatusBadge'
import { formatTime, getScoreColor } from '../../utils/format'
import type { TestRun } from '../../utils/api'

interface ComparisonTableProps {
  runA: TestRun
  runB: TestRun
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

export function ComparisonTable({ runA, runB }: ComparisonTableProps) {
  const scoreDelta = runB.resilience_score - runA.resilience_score
  const rtoDelta = runB.rto_seconds - runA.rto_seconds
  const rpoDelta = runB.rpo_seconds - runA.rpo_seconds

  return (
    <div className="card animate-in animate-in-delay-2" style={{ padding: 0, overflow: 'hidden', marginBottom: 'var(--space-6)' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{
              textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)',
              letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)', width: '25%',
            }}>
              METRIC
            </th>
            <th style={{
              textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)',
              letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)',
            }}>
              <div style={{ fontFamily: 'var(--font-mono)' }}>{runA.run_id}</div>
            </th>
            <th style={{
              textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)',
              letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)',
            }}>
              <div style={{ fontFamily: 'var(--font-mono)' }}>{runB.run_id}</div>
            </th>
            <th style={{
              textAlign: 'right', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)',
              letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)',
            }}>
              DELTA
            </th>
          </tr>
        </thead>
        <tbody>
          <CompareRow
            label="Score"
            valueA={runA.resilience_score.toString()}
            valueB={runB.resilience_score.toString()}
            delta={scoreDelta}
            inverse={false}
            renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 600, color: getScoreColor(parseInt(v)) }}>{v}</span>}
          />
          <CompareRow
            label="RTO"
            valueA={formatTime(runA.rto_seconds)}
            valueB={formatTime(runB.rto_seconds)}
            delta={rtoDelta}
            inverse={true}
            renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{v}</span>}
          />
          <CompareRow
            label="RPO"
            valueA={formatTime(runA.rpo_seconds)}
            valueB={formatTime(runB.rpo_seconds)}
            delta={rpoDelta}
            inverse={true}
            renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{v}</span>}
          />
          <CompareRow
            label="Status"
            valueA={runA.status}
            valueB={runB.status}
            delta={0}
            renderValue={(v) => <StatusBadge status={v} size="sm" />}
          />
          <CompareRow
            label="RTO Target"
            valueA={formatTime(runA.rto_target)}
            valueB={formatTime(runB.rto_target)}
            delta={0}
            renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-muted)' }}>{v}</span>}
          />
          <CompareRow
            label="RPO Target"
            valueA={formatTime(runA.rpo_target)}
            valueB={formatTime(runB.rpo_target)}
            delta={0}
            renderValue={(v) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-muted)' }}>{v}</span>}
          />
        </tbody>
      </table>
    </div>
  )
}
