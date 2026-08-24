import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { ArrowLeft, FileText, GitCompare, Download } from 'lucide-react'
import { StatusBadge } from '../components/shared/StatusBadge'
import { formatTime, formatTimestamp, getScoreColor } from '../utils/format'
import type { TestRun } from '../utils/api'

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
      <div className="skeleton skeleton-text" style={{ width: 100, height: 14, marginBottom: 'var(--space-6)' }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
        <div className="skeleton skeleton-heading" style={{ width: 140, height: 24, marginBottom: 0 }} />
        <div className="skeleton skeleton-pill" style={{ width: 64, height: 22, borderRadius: 9999 }} />
      </div>
      <div className="skeleton skeleton-text" style={{ width: '50%', marginBottom: 'var(--space-6)' }} />
      <div className="skeleton-card" style={{ height: 200, marginBottom: 'var(--space-6)' }} />
      <div className="skeleton-card" style={{ height: 120, marginBottom: 'var(--space-6)' }} />
      <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
        <div className="skeleton skeleton-pill" style={{ width: 140, height: 36 }} />
        <div className="skeleton skeleton-pill" style={{ width: 140, height: 36 }} />
      </div>
    </div>
  )
}

export default function RunDetail() {
  const [loading, setLoading] = useState(true)
  const [generatingPdf, setGeneratingPdf] = useState(false)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800)
    return () => clearTimeout(timer)
  }, [])

  const run = mockRun

  const handleGeneratePDF = async () => {
    setGeneratingPdf(true)
    try {
      // In production, call the API
      // const result = await apiClient.generatePDFReport({
      //   report_type: 'dr-test',
      //   report_id: run.run_id,
      // })
      // setPdfUrl(result.pdf_url)
      setTimeout(() => {
        setPdfUrl('#')
        setGeneratingPdf(false)
      }, 2000)
    } catch {
      setGeneratingPdf(false)
    }
  }

  if (loading) return <RunDetailSkeleton />

  return (
    <div className="page-container">
      {/* Back link */}
      <Link to="/runs" style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        fontSize: 13,
        color: 'var(--text-secondary)',
        marginBottom: 'var(--space-6)',
      }}>
        <ArrowLeft size={14} />
        Back to Runs
      </Link>

      {/* Header */}
      <div style={{ marginBottom: 'var(--space-6)' }} className="animate-in">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)' }}>
            Run Detail
          </h1>
          <StatusBadge status={run.status} />
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: 13, color: 'var(--text-muted)' }}>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{run.run_id}</span>
          <span>·</span>
          <span>{formatTimestamp(run.timestamp)}</span>
          <span>·</span>
          <span>{run.fault_type}</span>
        </div>
      </div>

      {/* Score Card */}
      <div className="card animate-in animate-in-delay-1" style={{ padding: 'var(--space-8)', marginBottom: 'var(--space-6)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-8)' }}>
          {/* Left: Score */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>
              RESILIENCE SCORE
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 48,
                fontWeight: 700,
                color: getScoreColor(run.resilience_score),
              }}>
                {run.resilience_score}
              </span>
              <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>/100</span>
            </div>
          </div>

          {/* Right: Metrics */}
          <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <MetricRow label="RTO" actual={formatTime(run.rto_seconds)} target={formatTime(run.rto_target)} ok={run.rto_seconds <= run.rto_target} />
            <MetricRow label="RPO" actual={formatTime(run.rpo_seconds)} target={formatTime(run.rpo_target)} ok={run.rpo_seconds <= run.rpo_target} />
            <MetricRow label="TARGET" actual={run.target_resource} target="" ok={true} />
            <MetricRow label="FAULT" actual={run.fault_type} target="" ok={true} />
          </div>
        </div>
      </div>

      {/* Stage Timeline */}
      <div className="card animate-in animate-in-delay-2" style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-5)' }}>
          STAGE TIMELINE
        </h3>
        <div style={{ display: 'flex', gap: 0, position: 'relative' }}>
          {/* Progress line */}
          <div style={{
            position: 'absolute',
            top: 12,
            left: 24,
            right: 24,
            height: 2,
            background: 'var(--status-pass)',
          }} />

          {stages.map((stage) => (
            <div key={stage.name} style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              position: 'relative',
              zIndex: 1,
            }}>
              {/* Dot */}
              <div style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                background: 'var(--status-pass)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 8,
              }}>
                <div style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: 'var(--bg-card)',
                }} />
              </div>

              {/* Label */}
              <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>
                {stage.name}
              </span>

              {/* Timestamp */}
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                {stage.timestamp}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="animate-in animate-in-delay-3" style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
        <Link to={`/compare?a=${run.run_id}`} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <GitCompare size={14} />
          Compare with...
        </Link>
        <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <FileText size={14} />
          View Full Report
        </button>
        <button
          onClick={handleGeneratePDF}
          disabled={generatingPdf}
          className="btn btn-secondary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            opacity: generatingPdf ? 0.6 : 1,
          }}>
          {generatingPdf ? (
            <>
              <div style={{
                width: 14, height: 14,
                border: '2px solid rgba(255,255,255,0.3)',
                borderTopColor: 'white', borderRadius: '50%',
                animation: 'spin 1s linear infinite',
              }} />
              Generating PDF...
            </>
          ) : pdfUrl ? (
            <>
              <Download size={14} />
              Download PDF
            </>
          ) : (
            <>
              <Download size={14} />
              Generate PDF Report
            </>
          )}
        </button>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}

function MetricRow({ label, actual, target, ok }: { label: string; actual: string; target: string; ok: boolean }) {
  return (
    <div className="stagger-child card-interactive" style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '8px 12px',
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius-sm)',
    }}>
      <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
        {label}
      </span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>
          {actual}
        </span>
        {target && (
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            (target: {target})
          </span>
        )}
        <span style={{
          width: 18,
          height: 18,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: ok ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
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
