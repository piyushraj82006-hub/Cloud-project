import { useState, useEffect, useRef } from 'react'
import { StatusBadge } from '../shared/StatusBadge'
import { formatTime, getScoreColor } from '../../utils/format'
import type { TestRun } from '../../utils/api'

interface ScoreCardProps {
  run: TestRun
}

/** Animate a number from 0 to target over duration ms */
function useCountUp(target: number, duration = 800) {
  const [current, setCurrent] = useState(0)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const start = performance.now()
    const animate = (now: number) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCurrent(Math.round(eased * target))
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }
    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [target, duration])

  return current
}

function MetricCard({ label, value, target, ok }: { label: string; value: string; target: string; ok: boolean }) {
  return (
    <div className="stagger-child" style={{
      padding: '12px 16px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border-primary)',
      borderRadius: 'var(--radius-sm)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}>
      <div>
        <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 2 }}>
          {label}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
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
          width: 18,
          height: 18,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: ok ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
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

export function ScoreCard({ run }: ScoreCardProps) {
  const animatedScore = useCountUp(run.resilience_score)

  return (
    <div className="animate-in animate-in-delay-1" style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--space-6)',
      marginBottom: 'var(--space-8)',
    }}>
      {/* Score card */}
      <div className="card" style={{
        padding: 'var(--space-8)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-6)' }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4 }}>
              Latest Run
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-code)' }}>
              {run.run_id}
            </div>
          </div>
          <StatusBadge status={run.status} />
        </div>

        {/* Score with count-up animation */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 'var(--space-6)' }}>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 64,
            fontWeight: 700,
            color: getScoreColor(run.resilience_score),
            lineHeight: 1,
            letterSpacing: '-0.04em',
          }}>
            {animatedScore}
          </span>
          <span style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 400 }}>/100</span>
        </div>

        {/* Progress bar */}
        <div style={{
          height: 3,
          background: 'var(--border-primary)',
          borderRadius: 2,
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${run.resilience_score}%`,
            background: getScoreColor(run.resilience_score),
            borderRadius: 2,
            transition: 'width 1s ease',
          }} />
        </div>
      </div>

      {/* Metrics column */}
      <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <MetricCard label="RTO" value={formatTime(run.rto_seconds)} target={formatTime(run.rto_target)} ok={run.rto_seconds <= run.rto_target} />
        <MetricCard label="RPO" value={formatTime(run.rpo_seconds)} target={formatTime(run.rpo_target)} ok={run.rpo_seconds <= run.rpo_target} />
        <MetricCard label="Target" value={run.target_resource} target="" ok={true} />
        <MetricCard label="Fault" value={run.fault_type.replace('-', ' ')} target="" ok={true} />
      </div>
    </div>
  )
}
