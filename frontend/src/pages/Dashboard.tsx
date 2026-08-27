import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Play, ShieldCheck, ArrowRight, Lightbulb, Lightning, Globe, MagnifyingGlass, ArrowUpRight } from '@phosphor-icons/react'
import { ScoreCard } from '../components/Dashboard/ScoreCard'
import { TrendLine } from '../components/Dashboard/TrendLine'
import { QuickStats } from '../components/Dashboard/QuickStats'
import { RecentRuns } from '../components/Dashboard/RecentRuns'
import { ErrorState } from '../components/shared/ErrorState'
import { Skeleton } from '../components/shared/Skeleton'
import { apiClient } from '../utils/api'
import type { TestRun } from '../utils/api'

/* ─── Skeleton Loading State ─── */
function DashboardSkeleton() {
  return (
    <div className="page-container">
      <div style={{ marginBottom: 'var(--space-12)' }}>
        <Skeleton variant="pill" width={120} height={24} borderRadius={9999} style={{ marginBottom: 16 }} />
        <Skeleton variant="heading" />
        <Skeleton variant="text" width="70%" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)', marginBottom: 'var(--space-8)' }}>
        <Skeleton variant="card">
          <Skeleton variant="text" width={80} style={{ marginBottom: 24 }} />
          <Skeleton variant="score" style={{ marginBottom: 24 }} />
          <Skeleton height={3} borderRadius={9999} />
        </Skeleton>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {[1, 2, 3, 4].map(i => <Skeleton key={i} variant="metric" />)}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        {[1, 2, 3, 4].map(i => <Skeleton key={i} variant="pill" />)}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--space-6)' }}>
        <Skeleton variant="card" height={240} />
        <Skeleton variant="card" height={240} />
      </div>
    </div>
  )
}

/* ─── Empty State ─── */
function DashboardEmpty() {
  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 'var(--space-12)' }} className="animate-in">
        <div style={{
          width: 64, height: 64,
          borderRadius: 'var(--radius-lg)',
          background: 'var(--accent-muted)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto var(--space-6)',
        }}>
          <ShieldCheck size={28} weight="regular" style={{ color: 'var(--accent-primary)' }} />
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: 8 }}>
          Welcome to CloudGuard DR
        </h1>
        <p style={{ fontSize: 15, color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto', lineHeight: 1.6 }}>
          Automated disaster recovery testing. Prove your systems recover when it matters, not by assumption, but by actually breaking them.
        </p>
      </div>

      {/* Quick Start Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        {[
          { icon: Lightning, title: 'DR Test', desc: 'Break something, measure recovery time', color: '#EF4444', link: '/new-audit', action: 'Start Test' },
          { icon: Globe, title: 'Site Audit', desc: 'Health checks for any external URL', color: '#3B82F6', link: '/new-audit', action: 'Run Audit' },
          { icon: MagnifyingGlass, title: 'SEO Report', desc: 'Analyze meta tags, headings, performance', color: '#8B5CF6', link: '/new-audit', action: 'Run SEO Audit' },
        ].map((card, i) => (
          <Link key={i} to={card.link} className="card card-interactive animate-in" style={{
            padding: 'var(--space-6)',
            textDecoration: 'none',
            animationDelay: `${i * 0.1}s`,
          }}>
            <div style={{
              width: 40, height: 40, borderRadius: 'var(--radius-md)',
              background: `${card.color}15`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 'var(--space-4)',
            }}>
              <card.icon size={20} weight="regular" style={{ color: card.color }} />
            </div>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{card.title}</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 'var(--space-4)', lineHeight: 1.5 }}>{card.desc}</p>
            <span style={{ fontSize: 12, fontWeight: 500, color: card.color, display: 'flex', alignItems: 'center', gap: 4 }}>
              {card.action} <ArrowRight size={12} weight="bold" />
            </span>
          </Link>
        ))}
      </div>

      {/* How it works */}
      <div className="card animate-in animate-in-delay-2" style={{ padding: 'var(--space-8)' }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-6)' }}>
          How CloudGuard DR Works
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-6)' }}>
          {[
            { step: '1', label: 'Inject', desc: 'Terminate an EC2 instance or disrupt DNS/S3' },
            { step: '2', label: 'Monitor', desc: 'Poll health checks until recovery or timeout' },
            { step: '3', label: 'Measure', desc: 'Calculate actual RTO and RPO' },
            { step: '4', label: 'Score', desc: 'Convert to 0-100 resilience score' },
          ].map((item, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{
                width: 32, height: 32, borderRadius: '50%',
                background: 'var(--accent-muted)',
                border: '1px solid var(--accent-primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto var(--space-3)',
                fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700,
                color: 'var(--accent-primary)',
              }}>
                {item.step}
              </div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{item.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.4 }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div style={{ textAlign: 'center', marginTop: 'var(--space-8)' }} className="animate-in animate-in-delay-3">
        <Link to="/new-audit" className="btn btn-primary" style={{ padding: '14px 32px', fontSize: 14 }}>
          <Play size={14} weight="fill" />
          Run Your First Test
        </Link>
      </div>
    </div>
  )
}

/* ─── Main Dashboard ─── */
export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [runs, setRuns] = useState<TestRun[]>([])
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [comparisons, setComparisons] = useState<any[]>([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [runsResult, recsResult, cmpResult] = await Promise.allSettled([
        apiClient.getRuns({ limit: 20 }),
        apiClient.getRecommendations({ limit: 5 }),
        apiClient.listComparisons({ limit: 5 }),
      ])

      if (runsResult.status === 'fulfilled') {
        setRuns(runsResult.value.runs || [])
      } else {
        console.error('Failed to load runs:', runsResult.reason)
      }

      if (recsResult.status === 'fulfilled') {
        setRecommendations(recsResult.value.recommendations || [])
      }

      if (cmpResult.status === 'fulfilled') {
        setComparisons(cmpResult.value.comparisons || [])
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <DashboardSkeleton />

  if (error) return (
    <div className="page-container">
      <ErrorState title="Couldn't load dashboard" description={error} onRetry={loadData} />
    </div>
  )

  if (runs.length === 0) return <DashboardEmpty />

  const latestRun = runs[0]

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-12)' }} className="animate-in">
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '4px 12px',
          background: latestRun.status === 'Passed' ? 'rgba(34, 197, 94, 0.08)' : 'rgba(239, 68, 68, 0.08)',
          border: `1px solid ${latestRun.status === 'Passed' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
          borderRadius: 'var(--radius-sm)',
          fontSize: 11, fontWeight: 500,
          color: latestRun.status === 'Passed' ? '#22C55E' : '#EF4444',
          marginBottom: 12,
        }}>
          <span className={`status-dot ${latestRun.status === 'Passed' ? 'status-dot-live' : 'status-dot-fail'}`} />
          {latestRun.status === 'Passed' ? 'Systems Operational' : 'Recovery Needed'}
        </div>
        <h1 style={{
          fontSize: 28, fontWeight: 600, color: 'var(--text-primary)',
          letterSpacing: '-0.02em', lineHeight: 1.2, marginBottom: 6,
        }}>
          Resilience Overview
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, maxWidth: 480 }}>
          Automated disaster recovery testing. Prove your systems recover when it matters.
        </p>
      </div>

      {/* Hero Score Card */}
      <ScoreCard run={latestRun} />

      {/* Quick Stats */}
      <QuickStats runs={runs} />

      {/* Recommendations (if any) */}
      {recommendations.length > 0 && (
        <div className="animate-in animate-in-delay-2" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="card" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
            <Lightbulb size={16} weight="regular" style={{ color: '#F59E0B', flexShrink: 0 }} />
            <div style={{ flex: 1, fontSize: 12, color: 'var(--text-secondary)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>{recommendations.length} recommendation{recommendations.length > 1 ? 's' : ''}</strong>
              {' - '}
              {recommendations[0].title}
            </div>
            <Link to="/compare" style={{ fontSize: 11, color: 'var(--accent-primary)', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}>
              View insights <ArrowRight size={12} weight="bold" />
            </Link>
          </div>
        </div>
      )}

      {/* Trend + Recent Runs */}
      <div className="animate-in animate-in-delay-3" style={{
        display: 'grid', gridTemplateColumns: '2fr 1fr',
        gap: 'var(--space-6)', marginBottom: 'var(--space-8)',
      }}>
        <div className="card" style={{ padding: 'var(--space-8)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Resilience Trend</h3>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Last {runs.length} runs
            </span>
          </div>
          <TrendLine runs={runs} />
        </div>
        <RecentRuns runs={runs} />
      </div>

      {/* Recent Comparisons */}
      {comparisons.length > 0 && (
        <div className="animate-in animate-in-delay-3" style={{ marginBottom: 'var(--space-8)' }}>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--border-primary)' }}>
              <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Recent Site Comparisons</h3>
              <Link to="/compare" style={{ fontSize: 11, color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                Compare more <ArrowUpRight size={12} weight="bold" />
              </Link>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '10px 20px', borderBottom: '1px solid var(--border-muted)' }}>SITE A</th>
                  <th style={{ textAlign: 'center', padding: '10px 20px', borderBottom: '1px solid var(--border-muted)' }}></th>
                  <th style={{ textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '10px 20px', borderBottom: '1px solid var(--border-muted)' }}>SITE B</th>
                  <th style={{ textAlign: 'center', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '10px 20px', borderBottom: '1px solid var(--border-muted)' }}>W / T / L</th>
                  <th style={{ textAlign: 'right', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '10px 20px', borderBottom: '1px solid var(--border-muted)' }}>TIME</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((cmp: any) => {
                  const timeAgo = (dateStr: string) => {
                    const diff = Date.now() - new Date(dateStr).getTime()
                    const mins = Math.floor(diff / 60000)
                    if (mins < 1) return 'just now'
                    if (mins < 60) return `${mins}m ago`
                    const hours = Math.floor(mins / 60)
                    if (hours < 24) return `${hours}h ago`
                    const days = Math.floor(hours / 24)
                    return `${days}d ago`
                  }
                  return (
                    <tr key={cmp.comparison_id} className="table-row-interactive" style={{ cursor: 'pointer' }}>
                      <td style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-muted)' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>{cmp.domain_a}</span>
                      </td>
                      <td style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-muted)', textAlign: 'center' }}>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>vs</span>
                      </td>
                      <td style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-muted)' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>{cmp.domain_b}</span>
                      </td>
                      <td style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-muted)', textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                        <span style={{ color: 'var(--status-pass)' }}>{cmp.summary?.a_wins ?? 0}</span>
                        <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>/</span>
                        <span style={{ color: 'var(--text-muted)' }}>{cmp.summary?.ties ?? 0}</span>
                        <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>/</span>
                        <span style={{ color: 'var(--status-fail)' }}>{cmp.summary?.b_wins ?? 0}</span>
                      </td>
                      <td style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-muted)', textAlign: 'right' }}>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{timeAgo(cmp.created_at)}</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="animate-in animate-in-delay-4" style={{ display: 'flex', gap: 'var(--space-3)' }}>
        <Link to="/new-audit" className="btn btn-primary" style={{ padding: '12px 24px' }}>
          <Play size={14} weight="fill" />
          Run New Test
        </Link>
        <Link to="/compare" className="btn btn-secondary" style={{ padding: '12px 24px' }}>
          Compare Sites
        </Link>
      </div>
    </div>
  )
}
