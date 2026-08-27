import { Lightning, Globe, MagnifyingGlass, ChartBar } from '@phosphor-icons/react'

export type AuditType = 'dr-test' | 'external' | 'seo' | 'competitor'

interface AuditTypeToggleProps {
  value: AuditType
  onChange: (type: AuditType) => void
}

const options: { value: AuditType; icon: typeof Lightning; title: string; desc: string }[] = [
  { value: 'dr-test', icon: Lightning, title: 'Full DR Test (Fault Injection)', desc: 'Break something, measure recovery - EC2, DNS, S3, or security group' },
  { value: 'external', icon: Globe, title: 'External Site Audit (Health Check Only)', desc: 'Non-intrusive checks: HTTPS, DNS, response time' },
  { value: 'seo', icon: MagnifyingGlass, title: 'SEO Audit Report', desc: 'Analyze meta tags, headings, images, performance, social tags' },
  { value: 'competitor', icon: ChartBar, title: 'Competitive Analysis', desc: 'Compare against competitors, find gaps, get strategic opportunities' },
]

export function AuditTypeToggle({ value, onChange }: AuditTypeToggleProps) {
  return (
    <div className="card animate-in animate-in-delay-1" style={{ marginBottom: 'var(--space-6)' }}>
      <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
        AUDIT TYPE
      </h3>
      <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {options.map(opt => (
          <label
            key={opt.value}
            className="stagger-child card-interactive"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              padding: 'var(--space-4)',
              background: value === opt.value ? 'var(--accent-muted)' : 'var(--bg-secondary)',
              border: `1px solid ${value === opt.value ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
            }}
          >
            <input
              type="radio"
              name="auditType"
              value={opt.value}
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
              style={{ accentColor: 'var(--accent-primary)' }}
            />
            <opt.icon size={16} weight="regular" style={{ color: 'var(--accent-primary)' }} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{opt.title}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{opt.desc}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}
