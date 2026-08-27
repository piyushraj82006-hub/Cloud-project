import { Link } from 'react-router-dom'
import { ArrowLeft } from '@phosphor-icons/react'
import { StatusBadge } from '../shared/StatusBadge'
import { formatTimestamp } from '../../utils/format'
import type { TestRun } from '../../utils/api'

interface RunHeaderProps {
  run: TestRun
}

export function RunHeader({ run }: RunHeaderProps) {
  return (
    <>
      {/* Back link */}
      <Link to="/runs" style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        fontSize: 13,
        color: 'var(--text-secondary)',
        marginBottom: 'var(--space-6)',
      }}>
        <ArrowLeft size={14} weight="bold" />
        Back to Runs
      </Link>

      {/* Header */}
      <div style={{ marginBottom: 'var(--space-6)' }} className="animate-in">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)' }}>
            Run Detail
          </h1>
          <StatusBadge status={run.status} />
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: 13, color: 'var(--text-muted)' }}>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{run.run_id}</span>
          <span>·</span>
          <span>{formatTimestamp(run.timestamp)}</span>
          <span>·</span>
          <span>{run.fault_type}</span>
        </div>
      </div>
    </>
  )
}
