import type { AuditType } from './AuditTypeToggle'

export type FaultType = 'ec2-termination' | 'dns-failover' | 's3-origin-block' | 'security-group'

interface AuditFormProps {
  auditType: AuditType
  targetUrl: string
  onTargetUrlChange: (url: string) => void
  industry: string
  onIndustryChange: (v: string) => void
  city: string
  onCityChange: (v: string) => void
  competitorUrls: string
  onCompetitorUrlsChange: (v: string) => void
  // DR-test specific
  faultType?: FaultType
  onFaultTypeChange?: (v: FaultType) => void
  port?: string
  onPortChange?: (v: string) => void
  securityGroupId?: string
  onSecurityGroupIdChange?: (v: string) => void
  bucketName?: string
  onBucketNameChange?: (v: string) => void
}

const faultOptions: { value: FaultType; label: string; desc: string }[] = [
  { value: 'ec2-termination', label: 'EC2 Termination', desc: 'Kill a tagged instance via FIS, measure auto-recovery' },
  { value: 'dns-failover', label: 'DNS Failover', desc: 'Disable Route53 health check to trigger failover' },
  { value: 's3-origin-block', label: 'S3 Origin Block', desc: 'Block S3 bucket access to test origin failover' },
  { value: 'security-group', label: 'Security Group', desc: 'Remove ingress rules on a port to block traffic' },
]

export function AuditForm({
  auditType,
  targetUrl,
  onTargetUrlChange,
  industry,
  onIndustryChange,
  city,
  onCityChange,
  competitorUrls,
  onCompetitorUrlsChange,
  faultType = 'ec2-termination',
  onFaultTypeChange,
  port = '443',
  onPortChange,
  securityGroupId = '',
  onSecurityGroupIdChange,
  bucketName = '',
  onBucketNameChange,
}: AuditFormProps) {
  const needsUrl = auditType === 'external' || auditType === 'seo' || auditType === 'competitor'
  const isDRTest = auditType === 'dr-test'

  return (
    <>
      {/* Target URL - shown for DR test (monitoring) and other audit types */}
      {(needsUrl || isDRTest) && (
        <div className="card animate-in" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
            {isDRTest ? 'TARGET SITE URL' : 'TARGET URL'}
          </h3>
          {isDRTest && (
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }}>
              The monitor will poll this URL to confirm recovery after the fault is injected.
            </p>
          )}
          <input
            type="url"
            value={targetUrl}
            onChange={e => onTargetUrlChange(e.target.value)}
            placeholder="https://example.com"
            className="form-input form-input-mono"
          />
        </div>
      )}

      {/* DR Test - Fault Type Selector */}
      {isDRTest && (
        <div className="card animate-in" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
            FAULT TYPE
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {faultOptions.map(opt => (
              <label
                key={opt.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)',
                  padding: 'var(--space-3) var(--space-4)',
                  background: faultType === opt.value ? 'var(--accent-muted)' : 'var(--bg-secondary)',
                  border: `1px solid ${faultType === opt.value ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <input
                  type="radio"
                  name="faultType"
                  value={opt.value}
                  checked={faultType === opt.value}
                  onChange={() => onFaultTypeChange?.(opt.value)}
                  style={{ accentColor: 'var(--accent-primary)' }}
                />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{opt.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* DR Test - Resource-specific fields */}
      {isDRTest && faultType === 'security-group' && (
        <div className="card animate-in" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
            SECURITY GROUP OPTIONS
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
                PORT
              </label>
              <input
                type="text"
                value={port}
                onChange={e => onPortChange?.(e.target.value)}
                placeholder="443"
                className="form-input form-input-mono"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
                SECURITY GROUP ID <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span>
              </label>
              <input
                type="text"
                value={securityGroupId}
                onChange={e => onSecurityGroupIdChange?.(e.target.value)}
                placeholder="sg-0abc123 - auto-discovers default SG"
                className="form-input form-input-mono"
              />
            </div>
          </div>
        </div>
      )}

      {isDRTest && faultType === 's3-origin-block' && (
        <div className="card animate-in" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
            S3 BUCKET
          </h3>
          <input
            type="text"
            value={bucketName}
            onChange={e => onBucketNameChange?.(e.target.value)}
            placeholder="my-static-site-bucket - auto-discovers from URL"
            className="form-input form-input-mono"
          />
        </div>
      )}

      {isDRTest && faultType === 'dns-failover' && (
        <div className="card animate-in" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
            DNS FAILOVER
          </h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            The health check will be auto-discovered from the target URL's domain.
            Make sure a Route53 health check exists for this domain.
          </p>
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
                  onChange={e => onIndustryChange(e.target.value)}
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
                  onChange={e => onCityChange(e.target.value)}
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
              onChange={e => onCompetitorUrlsChange(e.target.value)}
              placeholder={'Auto-discover from industry + city\n\nOr paste competitor URLs:\nhttps://competitor1.com\nhttps://competitor2.com'}
              rows={5}
              className="form-input form-input-mono"
              style={{ resize: 'vertical', fontSize: 13 }}
            />
          </div>
        </>
      )}
    </>
  )
}
