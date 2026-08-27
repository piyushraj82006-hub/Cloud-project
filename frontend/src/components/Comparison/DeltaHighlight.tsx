import { formatTime } from '../../utils/format'
import type { TestRun } from '../../utils/api'

interface DeltaHighlightProps {
  runA: TestRun
  runB: TestRun
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

export function DeltaHighlight({ runA, runB }: DeltaHighlightProps) {
  const scoreDelta = runB.resilience_score - runA.resilience_score
  const rtoDelta = runB.rto_seconds - runA.rto_seconds
  const rpoDelta = runB.rpo_seconds - runA.rpo_seconds

  return (
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
            text={`RTO exceeded target by ${formatTime(runB.rto_seconds - runB.rto_target)}`}
            improved={false}
          />
        )}
        {rpoDelta > 0 && (
          <DeltaItem
            text={`RPO exceeded target by ${formatTime(runB.rpo_seconds - runB.rpo_target)}`}
            improved={false}
          />
        )}
        {runB.status === 'Failed' && runA.status === 'Passed' && (
          <DeltaItem
            text="DNS failover is broken"
            improved={false}
          />
        )}
      </div>
    </div>
  )
}
