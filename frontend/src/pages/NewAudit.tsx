import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, FileText, WarningCircle, ArrowSquareOut, DownloadSimple, X, Sparkle, CheckCircle, Warning, Lightbulb, TrendUp, Users, Target, CaretDown, CaretRight } from '@phosphor-icons/react'
import { AuditTypeToggle, type AuditType } from '../components/NewAudit/AuditTypeToggle'
import { AuditForm, type FaultType } from '../components/NewAudit/AuditForm'
import { Skeleton } from '../components/shared/Skeleton'
import { apiClient, type CompetitorAnalysis } from '../utils/api'

/* ─── Skeleton Loading ─── */
function NewAuditSkeleton() {
  return (
    <div className="page-container" style={{ maxWidth: 600, margin: '0 auto' }}>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <Skeleton variant="text" width={90} height={14} borderRadius={4} style={{ marginBottom: 8 }} />
        <Skeleton variant="text" width="60%" height={14} />
      </div>
      <Skeleton variant="card">
        <Skeleton variant="text" width={100} height={10} style={{ marginBottom: 16 }} />
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} variant="metric" style={{ marginBottom: i < 4 ? 12 : 0 }} />
        ))}
      </Skeleton>
    </div>
  )
}

export default function NewAudit() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [auditType, setAuditType] = useState<AuditType>('dr-test')
  const [targetUrl, setTargetUrl] = useState('')
  const [industry, setIndustry] = useState('')
  const [city, setCity] = useState('')
  const [competitorUrls, setCompetitorUrls] = useState('')

  // DR-test specific state
  const [faultType, setFaultType] = useState<FaultType>('ec2-termination')
  const [port, setPort] = useState('443')
  const [securityGroupId, setSecurityGroupId] = useState('')
  const [bucketName, setBucketName] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 600)
    return () => clearTimeout(timer)
  }, [])

  const [auditResult, setAuditResult] = useState<null | {
    report_id: string
    seo_score: number
    pdf_url: string | null
    ai_insights: any
    target_url: string
    seo_checks: any
  }>(null)
  const [expandedChecks, setExpandedChecks] = useState<Record<string, boolean>>({})
  const [showConfirmNewAudit, setShowConfirmNewAudit] = useState(false)
  const [competitorResult, setCompetitorResult] = useState<CompetitorAnalysis | null>(null)
  const [auditError, setAuditError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // PDF state
  const [generatingPdf, setGeneratingPdf] = useState(false)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [showPdf, setShowPdf] = useState(false)

  const handleSubmit = async () => {
    setSubmitting(true)
    setAuditError(null)
    setAuditResult(null)
    setCompetitorResult(null)
    setPdfUrl(null)
    setShowPdf(false)
    try {
      if (auditType === 'seo') {
        const result = await apiClient.runSEOAudit(targetUrl)
        setAuditResult({
          report_id: result.report_id,
          seo_score: result.seo_score,
          pdf_url: result.pdf_url || null,
          ai_insights: result.ai_insights || null,
          target_url: result.target_url,
          seo_checks: result.seo_checks || null,
        })
        if (result.pdf_url) {
          setPdfUrl(result.pdf_url)
        }
      } else if (auditType === 'external') {
        await apiClient.runExternalAudit(targetUrl)
        navigate('/runs')
      } else if (auditType === 'competitor') {
        const result = await apiClient.runCompetitorAnalysis({
          target_url: targetUrl,
          industry: industry || undefined,
          city: city || undefined,
          competitor_urls: competitorUrls ? competitorUrls.split(',').map(u => u.trim()) : undefined,
        })
        setCompetitorResult(result)
      } else {
        // DR test — trigger fault injection
        await apiClient.runDRTest({
          fault_type: faultType,
          target_url: targetUrl || undefined,
          port: faultType === 'security-group' ? port : undefined,
          security_group_id: faultType === 'security-group' ? securityGroupId || undefined : undefined,
          bucket_name: faultType === 's3-origin-block' ? bucketName || undefined : undefined,
        })
        navigate('/runs')
      }
    } catch (err: any) {
      setAuditError(err?.response?.data?.error || err?.message || 'Audit failed')
    } finally {
      setSubmitting(false)
    }
  }

  const handleGeneratePDF = async () => {
    const reportType = auditResult ? 'seo' : competitorResult ? 'competitor' : null
    const reportId = auditResult?.report_id || competitorResult?.analysis_id
    if (!reportType || !reportId) return

    setGeneratingPdf(true)
    try {
      const result = await apiClient.generatePDFReport({
        report_type: reportType as 'seo' | 'competitor',
        report_id: reportId,
      })
      setPdfUrl(result.pdf_url)
      setShowPdf(true)
    } catch {
      // PDF generation failed
    } finally {
      setGeneratingPdf(false)
    }
  }

  const handleViewPdf = () => {
    if (pdfUrl) {
      setShowPdf(true)
    }
  }

  const handleClosePdf = () => {
    setShowPdf(false)
  }

  const hasUnsavedResults = !!(auditResult || competitorResult)

  const handleNewAuditClick = () => {
    if (hasUnsavedResults) {
      setShowConfirmNewAudit(true)
    } else {
      handleNewAudit()
    }
  }

  const handleNewAudit = () => {
    setAuditResult(null)
    setCompetitorResult(null)
    setPdfUrl(null)
    setShowPdf(false)
    setShowConfirmNewAudit(false)
    setExpandedChecks({})
    setTargetUrl('')
    setIndustry('')
    setCity('')
    setCompetitorUrls('')
    setAuditType('dr-test')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCancelNewAudit = () => {
    setShowConfirmNewAudit(false)
  }

  const toggleCheck = (key: string) => {
    setExpandedChecks(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const needsUrl = auditType === 'external' || auditType === 'seo' || auditType === 'competitor'

  if (loading) return <NewAuditSkeleton />

  const isSplitView = (auditResult && auditType === 'seo') || (competitorResult && auditType === 'competitor')
  const pdfLabel = auditResult ? 'SEO Report' : competitorResult ? 'Competitor Report' : 'Report'

  return (
    <div className={`audit-root ${isSplitView ? 'audit-root--split' : ''}`}>
      {/* ─── Left Panel ─── */}
      <div className="audit-left">
        <div className="page-container">
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
          <AuditTypeToggle value={auditType} onChange={setAuditType} />

          {/* Audit Form */}
          <AuditForm
            auditType={auditType}
            targetUrl={targetUrl}
            onTargetUrlChange={setTargetUrl}
            industry={industry}
            onIndustryChange={setIndustry}
            city={city}
            onCityChange={setCity}
            competitorUrls={competitorUrls}
            onCompetitorUrlsChange={setCompetitorUrls}
            faultType={faultType}
            onFaultTypeChange={setFaultType}
            port={port}
            onPortChange={setPort}
            securityGroupId={securityGroupId}
            onSecurityGroupIdChange={setSecurityGroupId}
            bucketName={bucketName}
            onBucketNameChange={setBucketName}
          />

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={submitting || (needsUrl && !targetUrl)}
            className="btn btn-primary"
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              padding: '12px 24px',
              fontSize: 14,
              opacity: submitting || (needsUrl && !targetUrl) ? 0.5 : 1,
              cursor: submitting || (needsUrl && !targetUrl) ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? (
              <>
                <div className="spinner" />
                Running...
              </>
            ) : (
              <>
                <Play size={14} weight="fill" />
                {auditType === 'dr-test' ? 'Start DR Test' : auditType === 'seo' ? 'Run SEO Audit' : auditType === 'competitor' ? 'Run Competitive Analysis' : 'Run Audit'}
              </>
            )}
          </button>

          {/* Audit Error */}
          {auditError && (
            <div className="animate-in" style={{
              marginTop: 'var(--space-4)',
              padding: '12px 14px',
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 13,
              color: '#EF4444',
            }}>
              <WarningCircle size={14} weight="regular" />
              {auditError}
            </div>
          )}

          {/* ─── SEO Audit Result (Left Panel) ─── */}
          {auditResult && auditType === 'seo' && (
            <div className="animate-in" style={{
              marginTop: 'var(--space-6)',
              padding: 'var(--space-6)',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-md)',
            }}>
              {/* Score */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 'var(--space-4)' }}>
                <div style={{
                  fontSize: 36,
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  color: auditResult.seo_score >= 70 ? '#22C55E' : auditResult.seo_score >= 50 ? '#F59E0B' : '#EF4444',
                }}>
                  {auditResult.seo_score}
                </div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                    SEO Score for {auditResult.target_url}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {auditResult.report_id}
                  </div>
                </div>
              </div>

              {/* AI Insights Summary */}
              {auditResult.ai_insights?.executive_summary && (
                <div style={{
                  padding: '10px 12px',
                  background: 'rgba(139, 92, 246, 0.06)',
                  border: '1px solid rgba(139, 92, 246, 0.15)',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: 'var(--space-4)',
                  fontSize: 13,
                  color: 'var(--text-secondary)',
                  lineHeight: 1.55,
                }}>
                  <strong style={{ color: '#8B5CF6' }}>AI Summary:</strong> {auditResult.ai_insights.executive_summary}
                </div>
              )}

              {/* Quick Wins */}
              {auditResult.ai_insights?.quick_wins?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#22C55E', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle size={10} weight="fill" />
                    Quick Wins
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                    {auditResult.ai_insights.quick_wins.map((w: string, i: number) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Medium Improvements */}
              {auditResult.ai_insights?.medium_improvements?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#F59E0B', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Warning size={10} weight="fill" />
                    Medium Improvements
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                    {auditResult.ai_insights.medium_improvements.map((w: string, i: number) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Opportunities */}
              {auditResult.ai_insights?.opportunities?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#8B5CF6', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Lightbulb size={10} weight="fill" />
                    Opportunities
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {auditResult.ai_insights.opportunities.map((opp: any, i: number) => (
                      <div key={i} style={{
                        padding: '8px 10px',
                        background: 'rgba(139, 92, 246, 0.04)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 12,
                        color: 'var(--text-secondary)',
                      }}>
                        <strong style={{ color: 'var(--text-primary)' }}>{opp.title}</strong>
                        {opp.description && <span> — {opp.description}</span>}
                        {opp.effort && (
                          <span style={{ marginLeft: 6, fontSize: 10, color: 'var(--text-muted)' }}>[{opp.effort}]</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Critical Actions */}
              {auditResult.ai_insights?.critical_actions?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#EF4444', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <WarningCircle size={10} weight="fill" />
                    Critical Actions
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {auditResult.ai_insights.critical_actions.map((action: any, i: number) => (
                      <div key={i} style={{
                        padding: '8px 10px',
                        background: 'rgba(239, 68, 68, 0.04)',
                        border: '1px solid rgba(239, 68, 68, 0.1)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 12,
                        color: 'var(--text-secondary)',
                      }}>
                        <strong style={{ color: 'var(--text-primary)' }}>{action.action}</strong>
                        {action.impact && <div style={{ fontSize: 11, marginTop: 2 }}>Impact: {action.impact}</div>}
                        {action.effort && <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Effort: {action.effort}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ─── SEO Check Details ─── */}
              {auditResult.seo_checks && (
                <div style={{ marginTop: 'var(--space-4)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path d="M2 2h5v5H2V2zm7 0h5v5H9V2zM2 9h5v5H2V9zm7 2.5a2.5 2.5 0 1 0 5 0 2.5 2.5 0 0 0-5 0z"/></svg>
                    SEO Check Details
                  </div>

                  {/* ── Meta & Basic ── */}
                  {(() => {
                    const metaChecks = [
                      { key: 'title', label: 'Title Tag', icon: '🏷️', details: (c: any) => [
                          c.value && { label: 'Content', value: c.value },
                          { label: 'Length', value: c.value ? `${c.value.length} chars` : 'N/A' },
                        ].filter(Boolean) },
                      { key: 'meta_description', label: 'Meta Description', icon: '📝', details: (c: any) => [
                          c.value && { label: 'Content', value: c.value },
                          { label: 'Length', value: c.value ? `${c.value.length} chars` : 'N/A' },
                        ].filter(Boolean) },
                      { key: 'viewport', label: 'Viewport', icon: '📱', details: (c: any) => [
                          c.value && { label: 'Value', value: c.value },
                        ].filter(Boolean) },
                      { key: 'canonical', label: 'Canonical URL', icon: '🔗', details: (c: any) => [
                          c.value && { label: 'URL', value: c.value },
                        ].filter(Boolean) },
                      { key: 'robots', label: 'Robots Meta', icon: '🤖', details: (c: any) => [
                          c.value && { label: 'Value', value: c.value },
                        ].filter(Boolean) },
                    ]
                    return (
                      <div style={{ marginBottom: 'var(--space-3)' }}>
                        <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4, paddingLeft: 2 }}>
                          Meta & Basic
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {metaChecks.map(({ key, label, icon, details }) => {
                            const check = auditResult.seo_checks[key]
                            if (!check) return null
                            const hasIssues = check.issues?.length > 0
                            const isExpanded = expandedChecks[key]
                            const detailItems = details(check)
                            return (
                              <div key={key}>
                                <button
                                  onClick={() => toggleCheck(key)}
                                  style={{
                                    width: '100%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8,
                                    padding: '7px 10px',
                                    background: isExpanded ? 'var(--bg-secondary)' : 'transparent',
                                    border: '1px solid ' + (isExpanded ? 'var(--border-primary)' : 'transparent'),
                                    borderRadius: 'var(--radius-sm)',
                                    cursor: 'pointer',
                                    transition: 'all 150ms ease',
                                    fontSize: 12,
                                    color: 'var(--text-primary)',
                                    textAlign: 'left',
                                  }}
                                >
                                  {isExpanded ? <CaretDown size={10} weight="bold" /> : <CaretRight size={10} weight="bold" />}
                                  <span>{icon}</span>
                                  <span style={{ flex: 1, fontWeight: 500 }}>{label}</span>
                                  {hasIssues ? (
                                    <span style={{ fontSize: 10, color: '#EF4444', fontWeight: 600 }}>{check.issues.length} issue{check.issues.length > 1 ? 's' : ''}</span>
                                  ) : (
                                    <CheckCircle size={12} weight="fill" color="#22C55E" />
                                  )}
                                </button>
                                {isExpanded && (
                                  <div style={{ padding: '8px 10px 8px 28px', fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                    {detailItems.map((item: any, di: number) => (
                                      <div key={di} style={{ marginBottom: 4 }}>
                                        <span style={{ color: 'var(--text-muted)' }}>{item.label}: </span>
                                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5 }}>{item.value}</span>
                                      </div>
                                    ))}
                                    {hasIssues && (
                                      <div style={{ marginTop: 6 }}>
                                        {check.issues.map((issue: string, ii: number) => (
                                          <div key={ii} style={{ display: 'flex', alignItems: 'flex-start', gap: 4, marginBottom: 2 }}>
                                            <WarningCircle size={10} color="#EF4444" style={{ marginTop: 2, flexShrink: 0 }} />
                                            <span>{issue}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })()}

                  {/* ── Content & Structure ── */}
                  {(() => {
                    const contentChecks = [
                      { key: 'headings', label: 'Headings', icon: '📑', details: (c: any) => [
                          { label: 'H1 Count', value: String(c.h1_count ?? 'N/A') },
                          { label: 'Has H1', value: c.has_h1 ? 'Yes' : 'No' },
                          { label: 'Has H2', value: c.has_h2 ? 'Yes' : 'No' },
                          { label: 'Hierarchy Valid', value: c.hierarchy_valid ? 'Yes' : 'No' },
                        ] },
                      { key: 'images', label: 'Images', icon: '🖼️', details: (c: any) => [
                          { label: 'Total', value: String(c.total ?? 'N/A') },
                          { label: 'With Alt Text', value: String(c.with_alt ?? 'N/A') },
                          { label: 'Without Alt Text', value: String(c.without_alt ?? 'N/A') },
                          { label: 'All Have Alt', value: c.all_have_alt ? 'Yes' : 'No' },
                        ] },
                      { key: 'links', label: 'Links', icon: '🔗', details: (c: any) => [
                          { label: 'Total', value: String(c.total ?? 'N/A') },
                          { label: 'Internal', value: String(c.internal ?? 'N/A') },
                          { label: 'External', value: String(c.external ?? 'N/A') },
                          { label: 'Nofollow', value: String(c.nofollow ?? 'N/A') },
                        ] },
                      { key: 'structured_data', label: 'Structured Data', icon: '📊', details: (c: any) => [
                          { label: 'Count', value: String(c.count ?? 'N/A') },
                          c.types?.length > 0 && { label: 'Types', value: c.types.join(', ') },
                        ].filter(Boolean) },
                    ]
                    return (
                      <div style={{ marginBottom: 'var(--space-3)' }}>
                        <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4, paddingLeft: 2 }}>
                          Content & Structure
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {contentChecks.map(({ key, label, icon, details }) => {
                            const check = auditResult.seo_checks[key]
                            if (!check) return null
                            const hasIssues = check.issues?.length > 0
                            const isExpanded = expandedChecks[key]
                            const detailItems = details(check)
                            return (
                              <div key={key}>
                                <button
                                  onClick={() => toggleCheck(key)}
                                  style={{
                                    width: '100%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8,
                                    padding: '7px 10px',
                                    background: isExpanded ? 'var(--bg-secondary)' : 'transparent',
                                    border: '1px solid ' + (isExpanded ? 'var(--border-primary)' : 'transparent'),
                                    borderRadius: 'var(--radius-sm)',
                                    cursor: 'pointer',
                                    transition: 'all 150ms ease',
                                    fontSize: 12,
                                    color: 'var(--text-primary)',
                                    textAlign: 'left',
                                  }}
                                >
                                  {isExpanded ? <CaretDown size={10} weight="bold" /> : <CaretRight size={10} weight="bold" />}
                                  <span>{icon}</span>
                                  <span style={{ flex: 1, fontWeight: 500 }}>{label}</span>
                                  {hasIssues ? (
                                    <span style={{ fontSize: 10, color: '#EF4444', fontWeight: 600 }}>{check.issues.length} issue{check.issues.length > 1 ? 's' : ''}</span>
                                  ) : (
                                    <CheckCircle size={12} weight="fill" color="#22C55E" />
                                  )}
                                </button>
                                {isExpanded && (
                                  <div style={{ padding: '8px 10px 8px 28px', fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                    {detailItems.map((item: any, di: number) => (
                                      <div key={di} style={{ marginBottom: 4 }}>
                                        <span style={{ color: 'var(--text-muted)' }}>{item.label}: </span>
                                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5 }}>{item.value}</span>
                                      </div>
                                    ))}
                                    {hasIssues && (
                                      <div style={{ marginTop: 6 }}>
                                        {check.issues.map((issue: string, ii: number) => (
                                          <div key={ii} style={{ display: 'flex', alignItems: 'flex-start', gap: 4, marginBottom: 2 }}>
                                            <WarningCircle size={10} color="#EF4444" style={{ marginTop: 2, flexShrink: 0 }} />
                                            <span>{issue}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })()}

                  {/* ── Social Tags ── */}
                  {(() => {
                    const socialChecks = [
                      { key: 'open_graph', label: 'Open Graph', icon: '📣', details: (c: any) => [
                          c.tags_found?.length > 0 && { label: 'Found', value: c.tags_found.join(', ') },
                          c.tags_missing?.length > 0 && { label: 'Missing', value: c.tags_missing.join(', ') },
                        ].filter(Boolean) },
                      { key: 'twitter_card', label: 'Twitter Card', icon: '🐦', details: (c: any) => [
                          c.tags_found?.length > 0 && { label: 'Found', value: c.tags_found.join(', ') },
                          c.tags_missing?.length > 0 && { label: 'Missing', value: c.tags_missing.join(', ') },
                        ].filter(Boolean) },
                    ]
                    return (
                      <div style={{ marginBottom: 'var(--space-3)' }}>
                        <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4, paddingLeft: 2 }}>
                          Social Tags
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {socialChecks.map(({ key, label, icon, details }) => {
                            const check = auditResult.seo_checks[key]
                            if (!check) return null
                            const hasIssues = check.issues?.length > 0
                            const isExpanded = expandedChecks[key]
                            const detailItems = details(check)
                            return (
                              <div key={key}>
                                <button
                                  onClick={() => toggleCheck(key)}
                                  style={{
                                    width: '100%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8,
                                    padding: '7px 10px',
                                    background: isExpanded ? 'var(--bg-secondary)' : 'transparent',
                                    border: '1px solid ' + (isExpanded ? 'var(--border-primary)' : 'transparent'),
                                    borderRadius: 'var(--radius-sm)',
                                    cursor: 'pointer',
                                    transition: 'all 150ms ease',
                                    fontSize: 12,
                                    color: 'var(--text-primary)',
                                    textAlign: 'left',
                                  }}
                                >
                                  {isExpanded ? <CaretDown size={10} weight="bold" /> : <CaretRight size={10} weight="bold" />}
                                  <span>{icon}</span>
                                  <span style={{ flex: 1, fontWeight: 500 }}>{label}</span>
                                  {hasIssues ? (
                                    <span style={{ fontSize: 10, color: '#EF4444', fontWeight: 600 }}>{check.issues.length} issue{check.issues.length > 1 ? 's' : ''}</span>
                                  ) : (
                                    <CheckCircle size={12} weight="fill" color="#22C55E" />
                                  )}
                                </button>
                                {isExpanded && (
                                  <div style={{ padding: '8px 10px 8px 28px', fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                    {detailItems.map((item: any, di: number) => (
                                      <div key={di} style={{ marginBottom: 4 }}>
                                        <span style={{ color: 'var(--text-muted)' }}>{item.label}: </span>
                                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5 }}>{item.value}</span>
                                      </div>
                                    ))}
                                    {hasIssues && (
                                      <div style={{ marginTop: 6 }}>
                                        {check.issues.map((issue: string, ii: number) => (
                                          <div key={ii} style={{ display: 'flex', alignItems: 'flex-start', gap: 4, marginBottom: 2 }}>
                                            <WarningCircle size={10} color="#EF4444" style={{ marginTop: 2, flexShrink: 0 }} />
                                            <span>{issue}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })()}

                  {/* ── Technical ── */}
                  {(() => {
                    const techChecks = [
                      { key: 'https', label: 'HTTPS', icon: '🔒', details: () => [] },
                      { key: 'performance', label: 'Performance', icon: '⚡', details: (c: any) => [
                          { label: 'Response Time', value: `${c.response_time_ms ?? 'N/A'}ms` },
                          { label: 'Fast', value: c.fast ? 'Yes' : 'No' },
                          { label: 'Content Size', value: `${c.content_size_kb ?? 'N/A'} KB` },
                        ] },
                    ]
                    return (
                      <div style={{ marginBottom: 'var(--space-3)' }}>
                        <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4, paddingLeft: 2 }}>
                          Technical
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {techChecks.map(({ key, label, icon, details }) => {
                            const check = auditResult.seo_checks[key]
                            if (!check) return null
                            const hasIssues = check.issues?.length > 0
                            const isExpanded = expandedChecks[key]
                            const detailItems = details(check)
                            return (
                              <div key={key}>
                                <button
                                  onClick={() => toggleCheck(key)}
                                  style={{
                                    width: '100%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8,
                                    padding: '7px 10px',
                                    background: isExpanded ? 'var(--bg-secondary)' : 'transparent',
                                    border: '1px solid ' + (isExpanded ? 'var(--border-primary)' : 'transparent'),
                                    borderRadius: 'var(--radius-sm)',
                                    cursor: 'pointer',
                                    transition: 'all 150ms ease',
                                    fontSize: 12,
                                    color: 'var(--text-primary)',
                                    textAlign: 'left',
                                  }}
                                >
                                  {isExpanded ? <CaretDown size={10} weight="bold" /> : <CaretRight size={10} weight="bold" />}
                                  <span>{icon}</span>
                                  <span style={{ flex: 1, fontWeight: 500 }}>{label}</span>
                                  {hasIssues ? (
                                    <span style={{ fontSize: 10, color: '#EF4444', fontWeight: 600 }}>{check.issues.length} issue{check.issues.length > 1 ? 's' : ''}</span>
                                  ) : (
                                    <CheckCircle size={12} weight="fill" color="#22C55E" />
                                  )}
                                </button>
                                {isExpanded && (
                                  <div style={{ padding: '8px 10px 8px 28px', fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                    {detailItems.map((item: any, di: number) => (
                                      <div key={di} style={{ marginBottom: 4 }}>
                                        <span style={{ color: 'var(--text-muted)' }}>{item.label}: </span>
                                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5 }}>{item.value}</span>
                                      </div>
                                    ))}
                                    {hasIssues && (
                                      <div style={{ marginTop: 6 }}>
                                        {check.issues.map((issue: string, ii: number) => (
                                          <div key={ii} style={{ display: 'flex', alignItems: 'flex-start', gap: 4, marginBottom: 2 }}>
                                            <WarningCircle size={10} color="#EF4444" style={{ marginTop: 2, flexShrink: 0 }} />
                                            <span>{issue}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })()}
                </div>
              )}

              {/* Actions */}
              <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginTop: 'var(--space-4)' }}>
                {pdfUrl ? (
                  <>
                    <button
                      onClick={handleViewPdf}
                      className="btn btn-primary"
                      style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                    >
                      <FileText size={14} weight="regular" />
                      View SEO Report
                    </button>
                    <a
                      href={pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary"
                      style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                    >
                      <DownloadSimple size={14} weight="regular" />
                      Download PDF
                    </a>
                  </>
                ) : (
                  <button
                    onClick={handleGeneratePDF}
                    disabled={generatingPdf}
                    className="btn btn-primary"
                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    {generatingPdf ? (
                      <>
                        <div className="spinner" />
                        Generating AI Report...
                      </>
                    ) : (
                      <>
                        <Sparkle size={14} weight="fill" />
                        Generate AI PDF Report
                      </>
                    )}
                  </button>
                )}
                <button
                  onClick={() => navigate('/runs')}
                  className="btn btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  View All Runs
                </button>
              </div>
            </div>
          )}

          {/* ─── Competitor Analysis Result (Left Panel) ─── */}
          {competitorResult && auditType === 'competitor' && (
            <div className="animate-in" style={{
              marginTop: 'var(--space-6)',
              padding: 'var(--space-6)',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-md)',
            }}>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 'var(--space-4)' }}>
                <Users size={18} weight="regular" color="#8B5CF6" />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                    Competitive Analysis
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {competitorResult.analysis_id} · {competitorResult.target_url}
                  </div>
                </div>
              </div>

              {/* Score Ranking Card */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 8,
                marginBottom: 'var(--space-4)',
              }}>
                <div style={{
                  padding: '10px 12px',
                  background: 'rgba(139, 92, 246, 0.06)',
                  border: '1px solid rgba(139, 92, 246, 0.12)',
                  borderRadius: 'var(--radius-sm)',
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                    Your Score
                  </div>
                  <div style={{
                    fontSize: 24,
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    color: competitorResult.gap_analysis.client_score >= 70 ? '#22C55E' : competitorResult.gap_analysis.client_score >= 50 ? '#F59E0B' : '#EF4444',
                  }}>
                    {competitorResult.gap_analysis.client_score}
                  </div>
                </div>
                <div style={{
                  padding: '10px 12px',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-sm)',
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                    Rank
                  </div>
                  <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                    {competitorResult.gap_analysis.client_rank}<span style={{ fontSize: 12, color: 'var(--text-muted)' }}>/{competitorResult.gap_analysis.total_sites}</span>
                  </div>
                </div>
                <div style={{
                  padding: '10px 12px',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-sm)',
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                    Avg. Competitor
                  </div>
                  <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                    {Math.round(competitorResult.gap_analysis.average_competitor_score)}
                  </div>
                </div>
              </div>

              {/* Competitor Score Bars */}
              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
                  Competitor Scores
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {Object.entries(competitorResult.gap_analysis.competitor_scores).map(([domain, score]) => (
                    <div key={domain} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ fontSize: 11, color: 'var(--text-secondary)', width: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flexShrink: 0 }}>
                        {domain}
                      </div>
                      <div style={{ flex: 1, height: 6, background: 'var(--bg-secondary)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${score}%`,
                          background: score >= 70 ? '#22C55E' : score >= 50 ? '#F59E0B' : '#EF4444',
                          borderRadius: 3,
                          transition: 'width 0.5s ease',
                        }} />
                      </div>
                      <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', width: 28, textAlign: 'right' }}>
                        {Math.round(score)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Feature Gaps */}
              {competitorResult.gap_analysis.feature_gaps?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#EF4444', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Target size={10} weight="fill" />
                    Feature Gaps
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {competitorResult.gap_analysis.feature_gaps.map((gap, i) => (
                      <div key={i} style={{
                        padding: '6px 10px',
                        background: gap.severity === 'critical' ? 'rgba(239, 68, 68, 0.04)' : gap.severity === 'important' ? 'rgba(245, 158, 11, 0.04)' : 'rgba(255, 255, 255, 0.02)',
                        border: gap.severity === 'critical' ? '1px solid rgba(239, 68, 68, 0.1)' : gap.severity === 'important' ? '1px solid rgba(245, 158, 11, 0.1)' : '1px solid var(--border-primary)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 12,
                        color: 'var(--text-secondary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}>
                        <div>
                          <strong style={{ color: 'var(--text-primary)' }}>{gap.feature}</strong>
                          {gap.client_has && (
                            <span style={{ marginLeft: 6, fontSize: 10, color: '#22C55E' }}>✓ You have</span>
                          )}
                        </div>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                          {gap.competitors_with}/{Object.keys(competitorResult.gap_analysis.competitor_scores).length} competitors
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Content Gaps */}
              {competitorResult.gap_analysis.content_gaps?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#F59E0B', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Warning size={10} weight="fill" />
                    Content Gaps
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {competitorResult.gap_analysis.content_gaps.map((gap, i) => (
                      <div key={i} style={{
                        padding: '8px 10px',
                        background: 'rgba(245, 158, 11, 0.04)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 12,
                        color: 'var(--text-secondary)',
                      }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{gap.gap}</div>
                        <div style={{ fontSize: 11 }}>{gap.detail}</div>
                        {gap.impact && (
                          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Impact: {gap.impact}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Strategic Opportunities */}
              {competitorResult.strategic_opportunities?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#8B5CF6', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Lightbulb size={10} weight="fill" />
                    Strategic Opportunities
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {competitorResult.strategic_opportunities.map((opp, i) => (
                      <div key={i} style={{
                        padding: '10px 12px',
                        background: 'rgba(139, 92, 246, 0.04)',
                        border: '1px solid rgba(139, 92, 246, 0.1)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 12,
                      }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{opp.title}</div>
                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.55 }}>{opp.description}</div>
                        <div style={{ display: 'flex', gap: 8, marginTop: 6, fontSize: 10 }}>
                          {opp.impact && (
                            <span style={{
                              display: 'inline-flex', alignItems: 'center', gap: 3,
                              padding: '2px 6px', borderRadius: 4,
                              background: 'rgba(34, 197, 94, 0.08)', color: '#22C55E',
                            }}>
                              <TrendUp size={8} weight="fill" /> {opp.impact}
                            </span>
                          )}
                          {opp.effort && (
                            <span style={{
                              display: 'inline-flex', alignItems: 'center', gap: 3,
                              padding: '2px 6px', borderRadius: 4,
                              background: 'rgba(245, 158, 11, 0.08)', color: '#F59E0B',
                            }}>
                              {opp.effort}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginTop: 'var(--space-4)' }}>
                {pdfUrl ? (
                  <>
                    <button
                      onClick={handleViewPdf}
                      className="btn btn-primary"
                      style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                    >
                      <FileText size={14} weight="regular" />
                      View Competitor Report
                    </button>
                    <a
                      href={pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary"
                      style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                    >
                      <DownloadSimple size={14} weight="regular" />
                      Download PDF
                    </a>
                  </>
                ) : (
                  <button
                    onClick={handleGeneratePDF}
                    disabled={generatingPdf}
                    className="btn btn-primary"
                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    {generatingPdf ? (
                      <>
                        <div className="spinner" />
                        Generating AI Report...
                      </>
                    ) : (
                      <>
                        <Sparkle size={14} weight="fill" />
                        Generate AI PDF Report
                      </>
                    )}
                  </button>
                )}
                <button
                  onClick={() => navigate('/runs')}
                  className="btn btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  View All Runs
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ─── Right Panel: PDF Viewer ─── */}
      {isSplitView && showPdf && pdfUrl && (
        <div className="audit-pdf-panel">
          <div className="pdf-panel-header">
            <div className="pdf-panel-title">
              <FileText size={14} weight="regular" />
              <span>{pdfLabel} — AI Generated</span>
            </div>
            <div className="pdf-panel-actions">
              <div style={{ position: 'relative' }}>
                <button
                  onClick={handleNewAuditClick}
                  className="pdf-panel-btn"
                  title="New Audit"
                  style={{ width: 'auto', padding: '0 8px', gap: 4, fontSize: 11, fontWeight: 500 }}
                >
                  <Play size={10} weight="fill" />
                  <span>New Audit</span>
                </button>
                {showConfirmNewAudit && (
                  <div className="audit-confirm-popover" style={{
                    position: 'absolute',
                    top: 'calc(100% + 6px)',
                    right: 0,
                    width: 220,
                    padding: '10px 12px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
                    zIndex: 100,
                    fontSize: 12,
                  }}>
                    <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <WarningCircle size={12} weight="fill" color="#F59E0B" />
                      Start new audit?
                    </div>
                    <div style={{ color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 8 }}>
                      Current results will be cleared.
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button
                        onClick={handleNewAudit}
                        className="btn btn-primary"
                        style={{ flex: 1, padding: '5px 10px', fontSize: 11, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
                      >
                        Confirm
                      </button>
                      <button
                        onClick={handleCancelNewAudit}
                        className="btn btn-secondary"
                        style={{ flex: 1, padding: '5px 10px', fontSize: 11, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
              <div style={{ width: 1, height: 16, background: 'var(--border-primary)', margin: '0 2px' }} />
              <a
                href={pdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="pdf-panel-btn"
                title="Open in new tab"
              >
                <ArrowSquareOut size={14} weight="regular" />
              </a>
              <a
                href={pdfUrl}
                download
                className="pdf-panel-btn"
                title="Download PDF"
              >
                <DownloadSimple size={14} weight="regular" />
              </a>
              <button
                onClick={handleClosePdf}
                className="pdf-panel-btn pdf-panel-btn--close"
                title="Close viewer"
              >
                <X size={14} weight="regular" />
              </button>
            </div>
          </div>
          <div className="pdf-panel-body">
            <iframe
              src={pdfUrl}
              title={pdfLabel}
              className="pdf-iframe"
            />
          </div>
        </div>
      )}

      {/* ─── Right Panel: Generating State ─── */}
      {isSplitView && generatingPdf && (
        <div className="audit-pdf-panel">
          <div className="pdf-panel-header">
            <div className="pdf-panel-title">
              <Sparkle size={14} weight="fill" />
              <span>Generating AI Report...</span>
            </div>
          </div>
          <div className="pdf-panel-body" style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            color: 'var(--text-muted)',
          }}>
            <div style={{
              width: 48,
              height: 48,
              border: '3px solid var(--border-primary)',
              borderTopColor: 'var(--accent-primary)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
            <div style={{ fontSize: 14, fontWeight: 500 }}>AI is generating your PDF report...</div>
            <div style={{ fontSize: 12 }}>This may take a moment</div>
          </div>
        </div>
      )}
    </div>
  )
}
