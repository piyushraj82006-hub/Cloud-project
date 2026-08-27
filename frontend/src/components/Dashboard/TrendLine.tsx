import { useState } from 'react'
import type { TestRun } from '../../utils/api'

interface TrendLineProps {
  runs: TestRun[]
}

interface TooltipData {
  run: TestRun
  x: number
  y: number
}

export function TrendLine({ runs }: TrendLineProps) {
  const [tooltip, setTooltip] = useState<TooltipData | null>(null)
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
            <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.08" />
            <stop offset="100%" stopColor="var(--accent-primary)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(val => {
          const y = padding.top + (1 - val / maxScore) * (height - padding.top - padding.bottom)
          return (
            <g key={val}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="var(--border-primary)" strokeWidth="0.2" />
              <text x={padding.left - 1.5} y={y + 0.8} fill="var(--text-muted)" fontSize="2.2" fontFamily="var(--font-mono)" textAnchor="end">{val}</text>
            </g>
          )
        })}

        {/* Fill area */}
        <path d={fillD} fill="url(#fillGrad)" />

        {/* Line */}
        <path d={pathD} fill="none" stroke="url(#lineGrad)" strokeWidth="0.7" strokeLinecap="round" strokeLinejoin="round" />

        {/* Dots */}
        {points.map((p, i) => (
          <g
            key={i}
            onMouseEnter={() => setTooltip({ run: p.run, x: p.x, y: p.y })}
            onMouseLeave={() => setTooltip(null)}
            style={{ cursor: 'pointer' }}
          >
            <circle cx={p.x} cy={p.y} r="3" fill="transparent" />
            <circle cx={p.x} cy={p.y} r="1.2" fill="var(--accent-primary)" />
          </g>
        ))}
      </svg>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'absolute',
          left: `${(tooltip.x / width) * 100}%`,
          top: `${(tooltip.y / height) * 100 - 20}%`,
          transform: 'translate(-50%, -100%)',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-sm)',
          padding: '6px 10px',
          pointerEvents: 'none',
          zIndex: 10,
          whiteSpace: 'nowrap',
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-code)', marginBottom: 2 }}>
            {tooltip.run.run_id}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, color: 'var(--accent-primary)' }}>
            {tooltip.run.resilience_score}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
            {new Date(tooltip.run.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </div>
        </div>
      )}

      {/* Labels */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
        {reversed.map((run, i) => (
          <span key={i} style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            {new Date(run.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        ))}
      </div>
    </div>
  )
}
