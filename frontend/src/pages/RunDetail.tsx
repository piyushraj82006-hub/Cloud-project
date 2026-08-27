import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { GitDiff, FileText, ArrowSquareOut, X, DownloadSimple, Play, WarningCircle } from '@phosphor-icons/react'
import { RunHeader } from '../components/RunDetail/RunHeader'
import { ScoreBreakdown } from '../components/RunDetail/ScoreBreakdown'
import { StageTimeline } from '../components/RunDetail/StageTimeline'
import { WeakPoints, type WeakPoint } from '../components/RunDetail/WeakPoints'
import { ErrorState } from '../components/shared/ErrorState'
import { Skeleton } from '../components/shared/Skeleton'
import { apiClient, type TestRun } from '../utils/api'

const mockRun: TestRun = {
  run_id: 'run-a1b2c3d4',
  timestamp: '2026-08-22T08:00:00Z',
  fault_type: 'ec2-termination',
  target_resource: 'i-0abc123def456',
  rto_seconds: 152,
  rpo_seconds: 45,
  resilience_score: 82,
  status: 'Passed',
  rto_target: 300,
  rpo_target: 60,
  report_s3_key: 'reports/run-a1b2c3d4/report.json',
}

const stages = [
  { name: 'Inject', timestamp: '08:00:00' },
  { name: 'Monitor', timestamp: '08:00:12' },
  { name: 'Measure', timestamp: '08:02:44' },
  { name: 'Score', timestamp: '08:02:45' },
  { name: 'Report', timestamp: '08:02:46' },
]

/* ─── Skeleton Loading ─── */
function RunDetailSkeleton() {
  return (
    <div className="page-container">
      <Skeleton variant="text" width={100} height={14} style={{ marginBottom: 'var(--space-6)' }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
        <Skeleton variant="heading" width={140} height={24} style={{ marginBottom: 0 }} />
        <Skeleton variant="pill" width={64} height={22} borderRadius={9999} />
      </div>
      <Skeleton variant="text" width="50%" style={{ marginBottom: 'var(--space-6)' }} />
      <Skeleton variant="card" height={200} style={{ marginBottom: 'var(--space-6)' }} />
      <Skeleton variant="card" height={120} style={{ marginBottom: 'var(--space-6)' }} />
      <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
        <Skeleton variant="pill" width={140} height={36} />
        <Skeleton variant="pill" width={140} height={36} />
      </div>
    </div>
  )
}

/** Detect report type from report data */
function detectReportType(reportData: any): 'dr-test' | 'seo' | 'competitor' {
  if (!reportData) return 'dr-test'
  if (reportData.seo_score !== undefined || reportData.seo_checks) return 'seo'
  if (reportData.site_analyses || reportData.gap_analysis || reportData.feature_matrix) return 'competitor'
  return 'dr-test'
}

/** Get the correct report_id for PDF generation */
function getReportIdForPdf(reportType: string, reportData: any, runId: string): string {
  if (reportType === 'seo' && reportData?.report_id) {
    return reportData.report_id
  }
  if (reportType === 'competitor' && reportData?.analysis_id) {
    return reportData.analysis_id
  }
  return runId
}

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, _setError] = useState<string | null>(null)
  const [run, setRun] = useState<TestRun>(mockRun)
  const [reportData, setReportData] = useState<any>(null)
  const [reportType, setReportType] = useState<'dr-test' | 'seo' | 'competitor'>('dr-test')
  const [generatingPdf, setGeneratingPdf] = useState(false)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [weakPoints, setWeakPoints] = useState<WeakPoint[]>([])
  const [showPdf, setShowPdf] = useState(false)
  const [showConfirmNewAudit, setShowConfirmNewAudit] = useState(false)

  useEffect(() => {
    async function fetchRun() {
      if (!runId) {
        setLoading(false)
        return
      }
      try {
        const [runData, reportResp] = await Promise.all([
          apiClient.getRun(runId),
          apiClient.getRunReport(runId).catch(() => null),
        ])
        setRun({ ...mockRun, ...runData })

        if (reportResp) {
          setReportData(reportResp)
          const detected = (reportResp.report_type as 'dr-test' | 'seo' | 'competitor') || detectReportType(reportResp)
          setReportType(detected)
          if (reportResp.pdf_url) {
            setPdfUrl(reportResp.pdf_url)
          }
          if (reportResp.weak_points && Array.isArray(reportResp.weak_points)) {
            setWeakPoints(reportResp.weak_points)
          }
        }
      } catch {
        setRun(mockRun)
      } finally {
        setLoading(false)
      }
    }
    fetchRun()
  }, [runId])

  const handleGeneratePDF = async () => {
    if (!run) return
    setGeneratingPdf(true)
    try {
      const reportId = getReportIdForPdf(reportType, reportData, run.run_id)
      const result = await apiClient.generatePDFReport({
        report_type: reportType,
        report_id: reportId,
      })
      setPdfUrl(result.pdf_url)
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

  const handleNewAuditClick = () => {
    setShowConfirmNewAudit(true)
  }

  const handleConfirmNewAudit = () => {
    setShowConfirmNewAudit(false)
    navigate('/new-audit')
  }

  const handleCancelNewAudit = () => {
    setShowConfirmNewAudit(false)
  }

  if (loading) return <RunDetailSkeleton />
  if (error) return (
    <div className="page-container">
      <ErrorState title="Couldn't load this run" description={error} onRetry={() => window.location.reload()} />
    </div>
  )

  const reportLabel = reportType === 'seo' ? 'SEO Report' : reportType === 'competitor' ? 'Competitor Report' : 'PDF Report'

  return (
    <div className={`run-detail-root ${showPdf ? 'run-detail-root--split' : ''}`}>
      {/* ─── Left Panel: Run Details ─── */}
      <div className="run-detail-left">
        <div className="page-container">
          <RunHeader run={run} />
          <ScoreBreakdown run={run} />
          <StageTimeline stages={stages} />

          {weakPoints.length > 0 && (
            <div className="animate-in animate-in-delay-2" style={{ marginBottom: 'var(--space-6)' }}>
              <WeakPoints weakPoints={weakPoints} />
            </div>
          )}

          {/* Actions */}
          <div className="animate-in animate-in-delay-3" style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
            <Link to={`/compare?a=${run.run_id}`} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <GitDiff size={14} weight="regular" />
              Compare with...
            </Link>

            {pdfUrl ? (
              <>
                <button
                  onClick={handleViewPdf}
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <FileText size={14} weight="regular" />
                  View {reportLabel}
                </button>
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <DownloadSimple size={14} weight="regular" />
                  Download
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
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText size={14} weight="regular" />
                    Generate {reportLabel}
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ─── Right Panel: PDF Viewer ─── */}
      {showPdf && pdfUrl && (
        <div className="run-detail-pdf-panel">
          <div className="pdf-panel-header">
            <div className="pdf-panel-title">
              <FileText size={14} weight="regular" />
              <span>{reportLabel}</span>
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
                  <div style={{
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
                      You'll be taken to the new audit form.
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button
                        onClick={handleConfirmNewAudit}
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
              title={reportLabel}
              className="pdf-iframe"
            />
          </div>
        </div>
      )}
    </div>
  )
}
