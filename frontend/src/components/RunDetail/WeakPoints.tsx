import { Warning, CaretDown, CaretUp, Clock, ShieldCheck } from '@phosphor-icons/react'
import { useState } from 'react'

export interface WeakPoint {
  category: string
  severity: 'critical' | 'high' | 'medium'
  title: string
  why_it_matters: string
  root_cause: string
  fix_steps: string[]
  estimated_effort?: string
  prevention?: string
}

interface WeakPointsProps {
  weakPoints: WeakPoint[]
}

const severityConfig = {
  critical: { color: '#EF4444', bg: 'rgba(239, 68, 68, 0.08)', border: 'rgba(239, 68, 68, 0.25)', label: 'CRITICAL' },
  high: { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.08)', border: 'rgba(245, 158, 11, 0.25)', label: 'HIGH' },
  medium: { color: '#FDE68A', bg: 'rgba(253, 230, 138, 0.06)', border: 'rgba(253, 230, 138, 0.2)', label: 'MEDIUM' },
}

function WeakPointCard({ finding, index }: { finding: WeakPoint; index: number }) {
  const [expanded, setExpanded] = useState(finding.severity === 'critical')
  const config = severityConfig[finding.severity] || severityConfig.medium

  return (
    <div
      className="stagger-child"
      style={{
        background: config.bg,
        border: `1px solid ${config.border}`,
        borderLeft: `3px solid ${config.color}`,
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        transition: 'all 0.2s ease',
      }}
    >
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '12px 14px',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        {/* Severity badge */}
        <span style={{
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: '0.08em',
          padding: '2px 6px',
          borderRadius: 3,
          background: `${config.color}20`,
          color: config.color,
          flexShrink: 0,
        }}>
          {config.label}
        </span>

        {/* Index */}
        <span style={{
          fontSize: 10,
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          flexShrink: 0,
        }}>
          #{index + 1}
        </span>

        {/* Title */}
        <span style={{
          fontSize: 13,
          fontWeight: 500,
          color: 'var(--text-primary)',
          flex: 1,
          lineHeight: 1.4,
        }}>
          {finding.title}
        </span>

        {/* Effort badge */}
        {finding.estimated_effort && (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 10,
            color: 'var(--text-muted)',
            background: 'var(--bg-secondary)',
            padding: '2px 6px',
            borderRadius: 3,
            flexShrink: 0,
          }}>
            <Clock size={9} weight="regular" />
            {finding.estimated_effort}
          </span>
        )}

        {/* Expand icon */}
        <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
          {expanded ? <CaretUp size={14} weight="bold" /> : <CaretDown size={14} weight="bold" />}
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ padding: '0 14px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Why it matters */}
          <div>
            <div style={{
              fontSize: 9,
              fontWeight: 600,
              color: '#EF4444',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              marginBottom: 3,
            }}>
              Why It Matters
            </div>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.55, margin: 0 }}>
              {finding.why_it_matters}
            </p>
          </div>

          {/* Root cause */}
          <div>
            <div style={{
              fontSize: 9,
              fontWeight: 600,
              color: '#F59E0B',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              marginBottom: 3,
            }}>
              Root Cause
            </div>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.55, margin: 0 }}>
              {finding.root_cause}
            </p>
          </div>

          {/* Fix steps */}
          {finding.fix_steps.length > 0 && (
            <div>
              <div style={{
                fontSize: 9,
                fontWeight: 600,
                color: '#22C55E',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                marginBottom: 3,
              }}>
                How To Fix
              </div>
              <ol style={{
                margin: 0,
                paddingLeft: 18,
                fontSize: 12.5,
                color: 'var(--text-secondary)',
                lineHeight: 1.7,
              }}>
                {finding.fix_steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Prevention */}
          {finding.prevention && (
            <div style={{
              padding: '8px 10px',
              background: 'rgba(16, 185, 129, 0.06)',
              border: '1px solid rgba(16, 185, 129, 0.15)',
              borderRadius: 'var(--radius-sm)',
            }}>
              <div style={{
                fontSize: 9,
                fontWeight: 600,
                color: '#22C55E',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                marginBottom: 3,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}>
                <ShieldCheck size={10} weight="regular" />
                Prevention
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                {finding.prevention}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function WeakPoints({ weakPoints }: WeakPointsProps) {
  if (!weakPoints || weakPoints.length === 0) return null

  const critical = weakPoints.filter(w => w.severity === 'critical').length
  const high = weakPoints.filter(w => w.severity === 'high').length
  const medium = weakPoints.filter(w => w.severity === 'medium').length

  return (
    <div
      className="card animate-in animate-in-delay-2"
      style={{
        padding: 'var(--space-6)',
        background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.04) 0%, var(--bg-card) 100%)',
        border: '1px solid rgba(239, 68, 68, 0.15)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-4)' }}>
        <div style={{
          width: 28,
          height: 28,
          borderRadius: 'var(--radius-sm)',
          background: 'rgba(239, 68, 68, 0.12)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Warning size={14} weight="fill" color="#EF4444" />
        </div>
        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Root Cause Analysis
          </h3>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', margin: 0 }}>
            {weakPoints.length} issue{weakPoints.length !== 1 ? 's' : ''} found
            {critical > 0 && <span style={{ color: '#EF4444' }}> · {critical} critical</span>}
            {high > 0 && <span style={{ color: '#F59E0B' }}> · {high} high</span>}
            {medium > 0 && <span style={{ color: '#FDE68A' }}> · {medium} medium</span>}
          </p>
        </div>
        <span style={{
          fontSize: 20,
          fontWeight: 700,
          fontFamily: 'var(--font-mono)',
          color: critical > 0 ? '#EF4444' : high > 0 ? '#F59E0B' : '#22C55E',
        }}>
          {weakPoints.length}
        </span>
      </div>

      {/* Findings */}
      <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {/* Sort: critical first, then high, then medium */}
        {[...weakPoints]
          .sort((a, b) => {
            const order = { critical: 0, high: 1, medium: 2 }
            return (order[a.severity] ?? 3) - (order[b.severity] ?? 3)
          })
          .map((finding, i) => (
            <WeakPointCard key={finding.category || i} finding={finding} index={i} />
          ))}
      </div>
    </div>
  )
}
