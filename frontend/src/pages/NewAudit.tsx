import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Globe, Zap, Search, BarChart3 } from 'lucide-react'

export default function NewAudit() {
  const navigate = useNavigate()
  const [auditType, setAuditType] = useState<'dr-test' | 'external' | 'seo' | 'competitor'>('dr-test')
  const [targetUrl, setTargetUrl] = useState('')
  const [industry, setIndustry] = useState('')
  const [city, setCity] = useState('')
  const [competitorUrls, setCompetitorUrls] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setLoading(false)
      navigate('/runs/run-new123')
    }, 2000)
  }

  return (
    <div className="page-container" style={{ maxWidth: 600, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
          New Audit
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
          Run a DR test or audit an external site
        </p>
      </div>

      {/* Audit Type Toggle */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
          AUDIT TYPE
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              padding: 'var(--space-4)',
              background: auditType === 'dr-test' ? 'var(--accent-muted)' : 'var(--bg-secondary)',
              border: `1px solid ${auditType === 'dr-test' ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            <input
              type="radio"
              name="auditType"
              value="dr-test"
              checked={auditType === 'dr-test'}
              onChange={() => setAuditType('dr-test')}
              style={{ accentColor: 'var(--accent-primary)' }}
            />
            <Zap size={16} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Full DR Test (Fault Injection)</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Terminates an EC2 instance and measures recovery</div>
            </div>
          </label>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              padding: 'var(--space-4)',
              background: auditType === 'external' ? 'var(--accent-muted)' : 'var(--bg-secondary)',
              border: `1px solid ${auditType === 'external' ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            <input
              type="radio"
              name="auditType"
              value="external"
              checked={auditType === 'external'}
              onChange={() => setAuditType('external')}
              style={{ accentColor: 'var(--accent-primary)' }}
            />
            <Globe size={16} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>External Site Audit (Health Check Only)</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Non-intrusive checks: HTTPS, DNS, response time</div>
            </div>
          </label>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              padding: 'var(--space-4)',
              background: auditType === 'seo' ? 'var(--accent-muted)' : 'var(--bg-secondary)',
              border: `1px solid ${auditType === 'seo' ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            <input
              type="radio"
              name="auditType"
              value="seo"
              checked={auditType === 'seo'}
              onChange={() => setAuditType('seo')}
              style={{ accentColor: 'var(--accent-primary)' }}
            />
            <Search size={16} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>SEO Audit Report</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Analyze meta tags, headings, images, performance, social tags</div>
            </div>
          </label>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              padding: 'var(--space-4)',
              background: auditType === 'competitor' ? 'var(--accent-muted)' : 'var(--bg-secondary)',
              border: `1px solid ${auditType === 'competitor' ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            <input
              type="radio"
              name="auditType"
              value="competitor"
              checked={auditType === 'competitor'}
              onChange={() => setAuditType('competitor')}
              style={{ accentColor: 'var(--accent-primary)' }}
            />
            <BarChart3 size={16} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Competitive Analysis</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Compare against competitors, find gaps, get strategic opportunities</div>
            </div>
          </label>
        </div>
      </div>

      {/* Target URL (for external / seo / competitor) */}
      {(auditType === 'external' || auditType === 'seo' || auditType === 'competitor') && (
        <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
            TARGET URL
          </h3>
          <input
            type="url"
            value={targetUrl}
            onChange={e => setTargetUrl(e.target.value)}
            placeholder="https://example.com"
            style={{
              width: '100%',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-primary)',
              color: 'var(--text-primary)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontFamily: 'var(--font-mono)',
              outline: 'none',
            }}
            onFocus={e => (e.target.style.borderColor = 'var(--accent-primary)')}
            onBlur={e => (e.target.style.borderColor = 'var(--border-primary)')}
          />
        </div>
      )}

      {/* Competitor-specific fields */}
      {auditType === 'competitor' && (
        <>
          <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
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
                  style={{
                    width: '100%',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-primary)',
                    color: 'var(--text-primary)',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 14,
                    outline: 'none',
                  }}
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
                  style={{
                    width: '100%',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-primary)',
                    color: 'var(--text-primary)',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 14,
                    outline: 'none',
                  }}
                />
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
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
              style={{
                width: '100%',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-primary)',
                color: 'var(--text-primary)',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                fontSize: 13,
                fontFamily: 'var(--font-mono)',
                outline: 'none',
                resize: 'vertical',
              }}
            />
          </div>
        </>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading || ((auditType === 'external' || auditType === 'seo' || auditType === 'competitor') && !targetUrl)}
        className="btn btn-primary"
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          padding: '12px 24px',
          fontSize: 14,
          opacity: loading || ((auditType === 'external' || auditType === 'seo' || auditType === 'competitor') && !targetUrl) ? 0.5 : 1,
          cursor: loading || ((auditType === 'external' || auditType === 'seo' || auditType === 'competitor') && !targetUrl) ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? (
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
