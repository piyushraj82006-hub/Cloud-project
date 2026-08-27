import { Link } from 'react-router-dom'
import { ArrowUpRight } from '@phosphor-icons/react'
import { StatusBadge } from '../shared/StatusBadge'
import { formatTimestamp, getScoreColor } from '../../utils/format'
import type { TestRun } from '../../utils/api'

interface RecentRunsProps {
  runs: TestRun[]
  maxItems?: number
}

export function RecentRuns({ runs, maxItems = 4 }: RecentRunsProps) {
  return (
    <div className="card" style={{ padding: 'var(--space-6)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
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
          View all <ArrowUpRight size={12} weight="bold" />
        </Link>
      </div>
      <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {runs.slice(0, maxItems).map((run) => (
          <Link
            key={run.run_id}
            to={`/runs/${run.run_id}`}
            className="stagger-child"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 10px',
              borderRadius: 'var(--radius-sm)',
              background: 'transparent',
              border: '1px solid transparent',
              textDecoration: 'none',
              transition: 'background 150ms ease',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
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
  )
}
