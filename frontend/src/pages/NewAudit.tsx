import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Globe, Zap, Search, BarChart3 } from 'lucide-react'

/* ─── Skeleton Loading ─── */
function NewAuditSkeleton() {
  return (
    <div className="page-container" style={{ maxWidth: 600, margin: '0 auto' }}>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div className="skeleton skeleton-text" style={{ width: 90, height: 14, borderRadius: 4, marginBottom: 8 }} />
        <div className="skeleton skeleton-text" style={{ width: '60%', height: 14 }} />
      </div>
      <div className="skeleton-card">
        <div className="skeleton skeleton-text" style={{ width: 100, height: 10, marginBottom: 16 }} />
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton skeleton-metric" style={{ marginBottom: i < 4 ? 12 : 0 }} />
        ))}
      </div>
    </div>
  )
}

export default function NewAudit() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [auditType, setAuditType] = useState<'dr-test' | 'external' | 'seo' | 'competitor'>('dr-test')
  const [targetUrl, setTargetUrl] = useState('')
  const [industry, setIndustry] = useState('')
  const [city, setCity] = useState('')
  const [competitorUrls, setCompetitorUrls] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 600)
    return () => clearTimeout(timer)
  }, [])

  const handleSubmit = async () => {
    setSubmitting(true)
    // Simulate API call
    setTimeout(() => {
      setSubmitting(false)
      navigate('/runs/run-new123')
    }, 2000)
  }

  if (loading) return <NewAuditSkeleton />

  return (
    <div className="page-container" style={{ maxWidth: 600, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-8)' }} className="animate-in">
        <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
          New Audit
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
          Run a DR test or audit an external site
        </p>
      </div>

      {/* Audit Type Toggle */}
      <div className="card animate-in animate-in-delay-1" style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
          AUDIT TYPE
        </h3>
        <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {([
            { value: 'dr-test' as const, icon: Zap, title: 'Full DR Test (Fault Injection)', desc: 'Terminates an EC2 instance and measures recovery' },
            { value: 'external' as const, icon: Globe, title: 'External Site Audit (Health Check Only)', desc: 'Non-intrusive checks: HTTPS, DNS, response time' },
            { value: 'seo' as const, icon: Search, title: 'SEO Audit Report', desc: 'Analyze meta tags, headings, images, performance, social tags' },
            { value: 'competitor' as const, icon: BarChart3, title: 'Competitive Analysis', desc: 'Compare against competitors, find gaps, get strategic opportunities' },
          ]).map(opt => (
            <label
              key={opt.value}
              className="stagger-child card-interactive"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-3)',
                padding: 'var(--space-4)',
                background: auditType === opt.value ? 'var(--accent-muted)' : 'var(--bg-secondary)',
                border: `1px solid ${auditType === opt.value ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
              }}
            >
              <input
                type="radio"
                name="auditType"
                value={opt.value}
                checked={auditType === opt.value}
                onChange={() => setAuditType(opt.value)}
                style={{ accentColor: 'var(--accent-primary)' }}
              />
              <opt.icon size={16} style={{ color: 'var(--accent-primary)' }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{opt.title}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{opt.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Target URL (for external / seo / competitor) */}
      {(auditType === 'external' || auditType === 'seo' || auditType === 'competitor') && (
        <div className="card animate-in" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
            TARGET URL
          </h3>
          <input
            type="url"
            value={targetUrl}
            onChange={e => setTargetUrl(e.target.value)}
            placeholder="https://example.com"
            className="form-input form-input-mono"
          />
        </div>
      )}

      {/* Competitor-specific fields */}
      {auditType === 'competitor' && (
        <>
          <div className="card animate-in" style={{ marginBottom: 'var(--space-6)' }}>
            <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
              BUSINESS INFO
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
              <div>
                <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
                  INDUSTRY / SERVICE
                </label>
                <input
                  type="text"
                  value={industry}
                  onChange={e => setIndustry(e.target.value)}
                  placeholder="e.g. plumbing, HVAC, roofing"
                  className="form-input"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
                  PRIMARY CITY
                </label>
                <input
                  type="text"
                  value={city}
                  onChange={e => setCity(e.target.value)}
                  placeholder="e.g. Austin, Denver, Miami"
                  className="form-input"
                />
              </div>
            </div>
          </div>

          <div className="card animate-in" style={{ marginBottom: 'var(--space-6)' }}>
            <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
              COMPETITOR URLs <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span>
            </h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }}>
              Leave empty to auto-discover competitors based on industry + city. Or enter URLs manually, one per line.
            </p>
            <textarea
              value={competitorUrls}
              onChange={e => setCompetitorUrls(e.target.value)}
              placeholder={'Auto-discover from industry + city\n\nOr paste competitor URLs:\nhttps://competitor1.com\nhttps://competitor2.com'}
              rows={5}
              className="form-input form-input-mono"
              style={{ resize: 'vertical', fontSize: 13 }}
            />
          </div>
        </>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={submitting || ((auditType === 'external' || auditType === 'seo' || auditType === 'competitor') && !targetUrl)}
        className="btn btn-primary"
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          padding: '12px 24px',
          fontSize: 14,
          opacity: submitting || ((auditType === 'external' || auditType === 'seo' || auditType === 'competitor') && !targetUrl) ? 0.5 : 1,
          cursor: submitting || ((auditType === 'external' || auditType === 'seo' || auditType === 'competitor') && !targetUrl) ? 'not-allowed' : 'pointer',
        }}
      >
        {submitting ? (
          <>
            <div style={{
              width: 14,
              height: 14,
              border: '2px solid rgba(255,255,255,0.3)',
              borderTopColor: 'white',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
            Running...
          </>
        ) : (
          <>
            <Play size={14} />
            {auditType === 'dr-test' ? 'Start DR Test' : auditType === 'seo' ? 'Run SEO Audit' : auditType === 'competitor' ? 'Run Competitive Analysis' : 'Run Audit'}
          </>
        )}
      </button>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
