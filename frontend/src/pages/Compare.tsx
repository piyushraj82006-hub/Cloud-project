import { useState, useEffect } from 'react'
import { MagnifyingGlass, ArrowsLeftRight, Check, Globe, Shield, Clock, FileText, DownloadSimple, ClockCounterClockwise, Lightbulb, Warning, WarningCircle, Info, TrendUp, TrendDown } from '@phosphor-icons/react'
import { Skeleton } from '../components/shared/Skeleton'
import { apiClient } from '../utils/api'

/* ─── Types ─── */
interface SiteMetrics {
  url: string
  status_code: number
  response_time_ms: number
  content_length: number
  https_valid: boolean
  ssl_expiry_days: number | null
  dns_resolves: boolean
  title: string | null
  title_length: number
  meta_description: string | null
  meta_desc_length: number
  has_h1: boolean
  h1_count: number
  h2_count: number
  h3_count: number
  total_images: number
  images_with_alt: number
  alt_text_ratio: number
  total_links: number
  internal_links: number
  external_links: number
  has_viewport: boolean
  has_og_tags: boolean
  og_tag_count: number
  has_twitter_card: boolean
  has_canonical: boolean
  has_schema: boolean
  has_robots: boolean
  has_robots_noindex: boolean
}

interface ComparisonHistoryItem {
  comparison_id: string
  created_at: string
  url_a: string
  url_b: string
  domain_a: string
  domain_b: string
  summary: { a_wins: number; b_wins: number; ties: number }
  parameters_compared: string[]
}

type CompareParam = {
  key: keyof SiteMetrics
  label: string
  icon: typeof Globe
  type: 'boolean' | 'number' | 'text'
  higherBetter?: boolean
}

const COMPARE_PARAMS: CompareParam[] = [
  { key: 'https_valid', label: 'HTTPS Valid', icon: Shield, type: 'boolean' },
  { key: 'ssl_expiry_days', label: 'SSL Expiry (days)', icon: Shield, type: 'number', higherBetter: true },
  { key: 'dns_resolves', label: 'DNS Resolves', icon: Globe, type: 'boolean' },
  { key: 'status_code', label: 'HTTP Status', icon: Globe, type: 'number' },
  { key: 'response_time_ms', label: 'Response Time', icon: Clock, type: 'number', higherBetter: false },
  { key: 'content_length', label: 'Content Size', icon: FileText, type: 'number', higherBetter: true },
  { key: 'title_length', label: 'Title Length', icon: FileText, type: 'number' },
  { key: 'meta_desc_length', label: 'Meta Desc Length', icon: FileText, type: 'number' },
  { key: 'has_h1', label: 'Has H1 Tag', icon: FileText, type: 'boolean' },
  { key: 'h1_count', label: 'H1 Count', icon: FileText, type: 'number' },
  { key: 'h2_count', label: 'H2 Count', icon: FileText, type: 'number', higherBetter: true },
  { key: 'h3_count', label: 'H3 Count', icon: FileText, type: 'number', higherBetter: true },
  { key: 'total_images', label: 'Total Images', icon: FileText, type: 'number', higherBetter: true },
  { key: 'images_with_alt', label: 'Images with Alt', icon: FileText, type: 'number', higherBetter: true },
  { key: 'alt_text_ratio', label: 'Alt Text Ratio', icon: FileText, type: 'number', higherBetter: true },
  { key: 'total_links', label: 'Total Links', icon: Globe, type: 'number', higherBetter: true },
  { key: 'internal_links', label: 'Internal Links', icon: Globe, type: 'number', higherBetter: true },
  { key: 'external_links', label: 'External Links', icon: Globe, type: 'number' },
  { key: 'has_viewport', label: 'Mobile Viewport', icon: Globe, type: 'boolean' },
  { key: 'has_og_tags', label: 'Open Graph Tags', icon: Globe, type: 'boolean' },
  { key: 'og_tag_count', label: 'OG Tag Count', icon: Globe, type: 'number', higherBetter: true },
  { key: 'has_twitter_card', label: 'Twitter Card', icon: Globe, type: 'boolean' },
  { key: 'has_canonical', label: 'Canonical URL', icon: Globe, type: 'boolean' },
  { key: 'has_schema', label: 'Structured Data', icon: Globe, type: 'boolean' },
  { key: 'has_robots', label: 'Robots Meta', icon: Globe, type: 'boolean' },
  { key: 'has_robots_noindex', label: 'Noindex', icon: Globe, type: 'boolean' },
]

const DEFAULT_PARAMS = [
  'https_valid', 'response_time_ms', 'status_code',
  'title_length', 'meta_desc_length', 'has_h1', 'alt_text_ratio',
  'has_viewport', 'has_og_tags', 'has_canonical', 'has_schema',
]

/* ─── CSV Export ─── */
function exportCSV(siteA: SiteMetrics, siteB: SiteMetrics, selectedParams: string[]) {
  const rows = [
    ['Metric', siteA.url, siteB.url, 'Winner'],
    ...selectedParams.map(key => {
      const param = COMPARE_PARAMS.find(p => p.key === key)
      if (!param) return [key, '', '', '']
      return [param.label, String(siteA[param.key] ?? '-'), String(siteB[param.key] ?? '-'), '']
    }),
  ]
  const csv = rows.map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `compare-${new URL(siteA.url).hostname}-vs-${new URL(siteB.url).hostname}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

/* ─── Param Toggle ─── */
function ParamToggle({ param, selected, onToggle }: { param: CompareParam; selected: boolean; onToggle: () => void }) {
  return (
    <label
      onClick={onToggle}
      style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 12px',
        background: selected ? 'var(--accent-muted)' : 'var(--bg-secondary)',
        border: `1px solid ${selected ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
        borderRadius: 'var(--radius-sm)', cursor: 'pointer',
        transition: 'all 0.15s ease', fontSize: 12,
        color: selected ? 'var(--text-primary)' : 'var(--text-muted)',
        userSelect: 'none',
      }}
    >
      <div style={{
        width: 16, height: 16, borderRadius: 4,
        border: `1.5px solid ${selected ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
        background: selected ? 'var(--accent-primary)' : 'transparent',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.15s ease',
      }}>
        {selected && <Check size={10} color="white" strokeWidth={3} />}
      </div>
      <param.icon size={13} style={{ color: selected ? 'var(--accent-primary)' : 'var(--text-muted)' }} />
      <span style={{ fontWeight: 500 }}>{param.label}</span>
    </label>
  )
}

/* ─── Result Row ─── */
function ResultRow({ param, valA, valB, serverWinner }: { param: CompareParam; valA: any; valB: any; serverWinner?: string }) {
  const formatValue = (v: any, type: string) => {
    if (v === null || v === undefined) return '-'
    if (type === 'boolean') return v ? '✓' : '✗'
    if (type === 'number' && param.key === 'response_time_ms') return `${v}ms`
    if (type === 'number' && param.key === 'ssl_expiry_days') return `${v}d`
    if (type === 'number' && param.key === 'content_length') return `${(v / 1024).toFixed(1)}KB`
    if (type === 'number' && param.key === 'alt_text_ratio') return `${(v * 100).toFixed(0)}%`
    if (type === 'number' && param.key === 'title_length') return `${v} chars`
    if (type === 'number' && param.key === 'meta_desc_length') return `${v} chars`
    return String(v)
  }

  const getWinner = () => {
    if (serverWinner) return serverWinner
    if (param.type === 'boolean') {
      if (valA === valB) return 'tie'
      return valA ? 'a' : 'b'
    }
    if (param.type === 'number' && typeof valA === 'number' && typeof valB === 'number') {
      if (valA === valB) return 'tie'
      if (param.higherBetter === undefined) return 'tie'
      return param.higherBetter ? (valA > valB ? 'a' : 'b') : (valA < valB ? 'a' : 'b')
    }
    return 'tie'
  }

  const winner = getWinner()

  return (
    <tr className="table-row-interactive">
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)', fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
        {param.label}
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)', fontFamily: 'var(--font-mono)', fontSize: 13, color: winner === 'a' ? 'var(--status-pass)' : 'var(--text-primary)', fontWeight: winner === 'a' ? 600 : 400 }}>
        {formatValue(valA, param.type)}
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)', fontFamily: 'var(--font-mono)', fontSize: 13, color: winner === 'b' ? 'var(--status-pass)' : 'var(--text-primary)', fontWeight: winner === 'b' ? 600 : 400 }}>
        {formatValue(valB, param.type)}
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)', textAlign: 'right', fontSize: 12 }}>
        {winner !== 'tie' && <span style={{ color: 'var(--status-pass)', fontWeight: 600 }}>✓</span>}
      </td>
    </tr>
  )
}

/* ─── History Row ─── */
function HistoryRow({ item, onLoad }: { item: ComparisonHistoryItem; onLoad: (id: string) => void }) {
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
    <tr className="table-row-interactive" onClick={() => onLoad(item.comparison_id)} style={{ cursor: 'pointer' }}>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>{item.domain_a}</div>
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)', textAlign: 'center' }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>vs</span>
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>{item.domain_b}</div>
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)', textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        <span style={{ color: 'var(--status-pass)' }}>{item.summary?.a_wins ?? 0}</span>
        <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>/</span>
        <span style={{ color: 'var(--text-muted)' }}>{item.summary?.ties ?? 0}</span>
        <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>/</span>
        <span style={{ color: 'var(--status-fail)' }}>{item.summary?.b_wins ?? 0}</span>
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-muted)', textAlign: 'right' }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{timeAgo(item.created_at)}</span>
      </td>
    </tr>
  )
}

/* ─── Skeleton ─── */
function CompareSkeleton() {
  return (
    <div className="page-container" style={{ maxWidth: 900, margin: '0 auto' }}>
      <Skeleton variant="text" width={140} height={14} borderRadius={4} style={{ marginBottom: 'var(--space-6)' }} />
      <div style={{ display: 'flex', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
        <Skeleton variant="pill" style={{ flex: 1, height: 44 }} />
        <Skeleton variant="pill" style={{ flex: 1, height: 44 }} />
      </div>
      <Skeleton variant="card" style={{ padding: 0 }}>
        {[1, 2, 3, 4, 5, 6].map(i => (
          <Skeleton key={i} height={48} style={{ borderBottom: i < 6 ? '1px solid var(--border-primary)' : 'none' }} />
        ))}
      </Skeleton>
    </div>
  )
}

/* ─── Main Component ─── */
export default function Compare() {
  const [loading, setLoading] = useState(true)
  const [comparing, setComparing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'new' | 'history' | 'insights'>('new')

  const [urlA, setUrlA] = useState('')
  const [urlB, setUrlB] = useState('')
  const [selectedParams, setSelectedParams] = useState<string[]>(DEFAULT_PARAMS)

  const [siteA, setSiteA] = useState<SiteMetrics | null>(null)
  const [siteB, setSiteB] = useState<SiteMetrics | null>(null)
  const [comparisonResult, setComparisonResult] = useState<Record<string, { a: any; b: any; winner: string }> | null>(null)

  const [history, setHistory] = useState<ComparisonHistoryItem[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [recSummary, setRecSummary] = useState<any>(null)
  const [recTrends, setRecTrends] = useState<any>(null)
  const [recLoading, setRecLoading] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (tab === 'history' && history.length === 0) loadHistory()
    if (tab === 'insights' && recommendations.length === 0) loadRecommendations()
  }, [tab])

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const result = await apiClient.listComparisons({ limit: 50 })
      setHistory(result.comparisons || [])
    } catch (err: any) {
      console.error('Failed to load comparison history:', err)
    } finally {
      setHistoryLoading(false)
    }
  }

  const loadComparison = async (comparisonId: string) => {
    try {
      const result = await apiClient.getComparison(comparisonId)
      setSiteA(result.site_a)
      setSiteB(result.site_b)
      setComparisonResult(result.comparison)
      setTab('new')
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load comparison')
    }
  }

  const loadRecommendations = async () => {
    setRecLoading(true)
    try {
      const result = await apiClient.getRecommendations({ limit: 50 })
      setRecommendations(result.recommendations || [])
      setRecSummary(result.summary || null)
      setRecTrends(result.trends || null)
    } catch (err: any) {
      console.error('Failed to load recommendations:', err)
    } finally {
      setRecLoading(false)
    }
  }

  const toggleParam = (key: string) => {
    setSelectedParams(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key])
  }

  const runComparison = async () => {
    if (!urlA || !urlB) return
    setComparing(true)
    setError(null)
    setSiteA(null)
    setSiteB(null)
    try {
      const result = await apiClient.compareSites({ url_a: urlA, url_b: urlB, parameters: selectedParams })
      setSiteA(result.site_a)
      setSiteB(result.site_b)
      if (result.comparison) setComparisonResult(result.comparison)
    } catch (err: any) {
      setError(err?.response?.data?.error || err?.message || 'Comparison failed')
    } finally {
      setComparing(false)
    }
  }

  if (loading) return <CompareSkeleton />

  return (
    <div className="page-container" style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }} className="animate-in">
        <div>
          <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
            Compare Sites
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Enter two URLs to compare their health, SEO, and performance
          </p>
        </div>
        {siteA && siteB && tab === 'new' && (
          <button onClick={() => exportCSV(siteA, siteB, selectedParams)} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px' }}>
            <DownloadSimple size={14} weight="regular" /> CSV
          </button>
        )}
      </div>

      {/* Tab Toggle */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 'var(--space-6)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: 4 }} className="animate-in animate-in-delay-1">
        {(['new', 'history', 'insights'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            padding: '10px 16px', fontSize: 13, fontWeight: 500,
            borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer',
            background: tab === t ? 'var(--bg-card)' : 'transparent',
            color: tab === t ? 'var(--text-primary)' : 'var(--text-muted)',
            boxShadow: tab === t ? '0 1px 3px rgba(0,0,0,0.2)' : 'none',
            transition: 'all 0.15s ease',
          }}>
            {t === 'new' ? <MagnifyingGlass size={14} weight="regular" /> : t === 'history' ? <ClockCounterClockwise size={14} weight="regular" /> : <Lightbulb size={14} weight="regular" />}
            {t === 'new' ? 'New Comparison' : t === 'history' ? 'History' : 'DR Insights'}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="animate-in" style={{ marginBottom: 'var(--space-6)', padding: '12px 14px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--radius-md)', fontSize: 13, color: '#EF4444' }}>
          {error}
        </div>
      )}

      {/* ─── History Tab ─── */}
      {tab === 'history' && (
        <div className="animate-in">
          {historyLoading ? (
            <Skeleton variant="card" style={{ padding: 0 }}>
              {[1, 2, 3].map(i => <Skeleton key={i} height={48} style={{ borderBottom: i < 3 ? '1px solid var(--border-primary)' : 'none' }} />)}
            </Skeleton>
          ) : history.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
              <ClockCounterClockwise size={24} weight="regular" style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }} />
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No comparisons yet. Run your first comparison to see it here.</p>
            </div>
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}>SITE A</th>
                    <th style={{ textAlign: 'center', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}></th>
                    <th style={{ textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}>SITE B</th>
                    <th style={{ textAlign: 'center', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}>W / T / L</th>
                    <th style={{ textAlign: 'right', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}>TIME</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(item => <HistoryRow key={item.comparison_id} item={item} onLoad={loadComparison} />)}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ─── Insights Tab ─── */}
      {tab === 'insights' && (
        <div className="animate-in">
          {recLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {[1, 2, 3].map(i => <Skeleton key={i} variant="card" height={80} />)}
            </div>
          ) : recommendations.length === 0 && !recSummary ? (
            <div className="card" style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
              <Lightbulb size={24} style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }} />
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No DR test data yet. Run some DR tests to get recommendations.</p>
            </div>
          ) : (
            <>
              {/* Summary Cards */}
              {recSummary && recSummary.total_runs > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
                  {[
                    { label: 'Pass Rate', value: `${recSummary.pass_rate}%`, color: recSummary.pass_rate >= 80 ? 'var(--status-pass)' : recSummary.pass_rate >= 50 ? '#F59E0B' : 'var(--status-fail)' },
                    { label: 'Avg Score', value: String(recSummary.avg_score), color: recSummary.avg_score >= 70 ? 'var(--status-pass)' : 'var(--status-fail)' },
                    { label: 'Avg RTO', value: `${recSummary.avg_rto}s`, color: 'var(--text-primary)' },
                    { label: 'Total Tests', value: String(recSummary.total_runs), color: 'var(--text-primary)' },
                  ].map((card, i) => (
                    <div key={i} className="card" style={{ padding: 'var(--space-4)', textAlign: 'center' }}>
                      <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>{card.label}</div>
                      <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-mono)', color: card.color }}>{card.value}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Trends */}
              {recTrends && (
                <div className="card" style={{ marginBottom: 'var(--space-4)', padding: '12px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', fontSize: 12 }}>
                    <span style={{ color: 'var(--text-muted)', fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase' }}>TRENDS:</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: recTrends.score === 'improving' ? 'var(--status-pass)' : recTrends.score === 'declining' ? 'var(--status-fail)' : 'var(--text-muted)' }}>
                      {recTrends.score === 'improving' ? <TrendUp size={13} weight="regular" /> : recTrends.score === 'declining' ? <TrendDown size={13} weight="regular" /> : null}
                      Score: {recTrends.score}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: recTrends.rto === 'improving' ? 'var(--status-pass)' : recTrends.rto === 'degrading' ? 'var(--status-fail)' : 'var(--text-muted)' }}>
                      {recTrends.rto === 'improving' ? <TrendUp size={13} weight="regular" /> : recTrends.rto === 'degrading' ? <TrendDown size={13} weight="regular" /> : null}
                      RTO: {recTrends.rto}
                    </span>
                  </div>
                </div>
              )}

              {/* Recommendations List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {recommendations.map((rec: any) => {
                  const severityConfig: Record<string, { bg: string; border: string; icon: typeof Warning; color: string }> = {
                    critical: { bg: 'rgba(239, 68, 68, 0.06)', border: 'rgba(239, 68, 68, 0.2)', icon: WarningCircle, color: '#EF4444' },
                    high: { bg: 'rgba(245, 158, 11, 0.06)', border: 'rgba(245, 158, 11, 0.2)', icon: Warning, color: '#F59E0B' },
                    medium: { bg: 'rgba(59, 130, 246, 0.06)', border: 'rgba(59, 130, 246, 0.2)', icon: Info, color: '#3B82F6' },
                    info: { bg: 'rgba(34, 197, 94, 0.06)', border: 'rgba(34, 197, 94, 0.2)', icon: Lightbulb, color: '#22C55E' },
                  }
                  const config = severityConfig[rec.severity] || severityConfig.info
                  const Icon = config.icon

                  return (
                    <div key={rec.id} className="card" style={{ padding: 'var(--space-4)', background: config.bg, border: `1px solid ${config.border}` }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
                        <Icon size={16} style={{ color: config.color, marginTop: 2, flexShrink: 0 }} />
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{rec.title}</span>
                            <span style={{ fontSize: 9, fontWeight: 600, color: config.color, letterSpacing: '0.08em', textTransform: 'uppercase', padding: '2px 6px', borderRadius: 4, background: `${config.color}15` }}>{rec.severity}</span>
                          </div>
                          <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 8px 0', lineHeight: 1.5 }}>{rec.description}</p>
                          <div style={{ fontSize: 12, color: 'var(--text-primary)', padding: '8px 10px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', borderLeft: `3px solid ${config.color}` }}>
                            <strong style={{ color: config.color, fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase' }}>Action:</strong> {rec.action}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      )}

      {/* ─── New Comparison Tab ─── */}
      {tab === 'new' && (
        <div className="animate-in">
          {/* URL Inputs */}
          <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
            <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>SITE A</label>
                <input type="url" value={urlA} onChange={e => setUrlA(e.target.value)} placeholder="https://example.com" className="form-input form-input-mono" style={{ fontSize: 13 }} />
              </div>
              <div style={{ paddingBottom: 6 }}><ArrowsLeftRight size={18} weight="regular" style={{ color: 'var(--text-muted)' }} /></div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>SITE B</label>
                <input type="url" value={urlB} onChange={e => setUrlB(e.target.value)} placeholder="https://competitor.com" className="form-input form-input-mono" style={{ fontSize: 13 }} />
              </div>
            </div>
          </div>

          {/* Compare Button */}
          <button onClick={runComparison} disabled={comparing || !urlA || !urlB} className="btn btn-primary" style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            padding: '12px 24px', fontSize: 14,
            opacity: comparing || !urlA || !urlB ? 0.5 : 1,
            cursor: comparing || !urlA || !urlB ? 'not-allowed' : 'pointer',
            marginBottom: 'var(--space-6)',
          }}>
            {comparing ? (
              <><div className="spinner" /> Analyzing both sites...</>
            ) : (
              <><MagnifyingGlass size={14} weight="regular" /> Compare Sites</>
            )}
          </button>

          {/* Parameter Selector (before results) */}
          {!siteA && !siteB && (
            <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
              <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>COMPARE PARAMETERS</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>Select which metrics to compare. Run the analysis to see results.</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                {COMPARE_PARAMS.map(param => <ParamToggle key={param.key} param={param} selected={selectedParams.includes(param.key)} onToggle={() => toggleParam(param.key)} />)}
              </div>
            </div>
          )}

          {/* Results */}
          {siteA && siteB && (
            <>
              {/* Compact Param Selector */}
              <div className="card" style={{ marginBottom: 'var(--space-4)', padding: '12px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>PARAMETERS:</span>
                  {COMPARE_PARAMS.map(param => <ParamToggle key={param.key} param={param} selected={selectedParams.includes(param.key)} onToggle={() => toggleParam(param.key)} />)}
                </div>
              </div>

              {/* Comparison Table */}
              <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 'var(--space-6)' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)', width: '25%' }}>METRIC</th>
                      <th style={{ textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{new URL(siteA.url).hostname}</div>
                      </th>
                      <th style={{ textAlign: 'left', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{new URL(siteB.url).hostname}</div>
                      </th>
                      <th style={{ textAlign: 'right', fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '12px 16px', borderBottom: '1px solid var(--border-primary)', width: '60px' }}>WINNER</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedParams.map(key => {
                      const param = COMPARE_PARAMS.find(p => p.key === key)
                      if (!param) return null
                      return <ResultRow key={key} param={param} valA={(siteA as any)[param.key]} valB={(siteB as any)[param.key]} serverWinner={comparisonResult?.[key]?.winner} />
                    })}
                  </tbody>
                </table>
              </div>

              {/* Summary */}
              <div className="card">
                <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>COMPARISON SUMMARY</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-4)' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                      {selectedParams.filter(k => comparisonResult?.[k]?.winner === 'a').length}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 4 }}>{new URL(siteA.url).hostname} wins</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {selectedParams.filter(k => comparisonResult?.[k]?.winner === 'tie').length}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 4 }}>Ties</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                      {selectedParams.filter(k => comparisonResult?.[k]?.winner === 'b').length}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 4 }}>{new URL(siteB.url).hostname} wins</div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      
    </div>
  )
}
