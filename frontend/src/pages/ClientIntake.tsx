import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserPlus, Building, MapPin, Globe, ArrowRight, Check, Lightning } from '@phosphor-icons/react'

interface IntakeFormData {
  business_name: string
  url: string
  industry: string
  primary_city: string
  state: string
  neighborhoods: string
  service_radius_miles: number
  geographic_scope: 'city' | 'regional' | 'multi-state'
  agency_name: string
  client_email: string
  known_competitors: string
  has_gbp: boolean
  gbp_review_count: number
  launch_status: 'live' | 'pre-launch' | 'rebuild'
  notes: string
}

const INDUSTRIES = [
  'Plumbing', 'HVAC', 'Roofing', 'Electrical', 'Landscaping',
  'Pest Control', 'Cleaning', 'Moving', 'Auto Repair', 'Dental',
  'Legal', 'Accounting', 'Real Estate', 'Insurance', 'Other',
]

/* ─── Skeleton Loading ─── */
function ClientIntakeSkeleton() {
  return (
    <div className="page-container" style={{ maxWidth: 600, margin: '0 auto' }}>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div className="skeleton skeleton-text" style={{ width: 110, height: 14, borderRadius: 4, marginBottom: 8 }} />
        <div className="skeleton skeleton-text" style={{ width: '50%', height: 14 }} />
      </div>
      <div style={{ display: 'flex', gap: 4, marginBottom: 'var(--space-6)' }}>
        {[1, 2, 3].map(s => (
          <div key={s} className="skeleton" style={{ flex: 1, height: 3, borderRadius: 2 }} />
        ))}
      </div>
      <div className="skeleton-card">
        <div className="skeleton skeleton-text" style={{ width: 140, height: 10, marginBottom: 20 }} />
        {[1, 2, 3].map(i => (
          <div key={i} style={{ marginBottom: 16 }}>
            <div className="skeleton skeleton-text" style={{ width: 80, height: 10, marginBottom: 8 }} />
            <div className="skeleton skeleton-pill" style={{ height: 40 }} />
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ClientIntake() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{
    client_id: string
    classification: { classification: string; business_type: string; geographic_scope: string; signals: string[]; location_page_strategy: string; keyword_tier_strategy: string }
    seo_strategy: { keyword_tiers: Array<{ tier: number; name: string; examples: string[] }>; content_priorities: Array<{ priority: number; action: string }>; technical_priorities: string[] }
  } | null>(null)

  const [form, setForm] = useState<IntakeFormData>({
    business_name: '',
    url: '',
    industry: '',
    primary_city: '',
    state: '',
    neighborhoods: '',
    service_radius_miles: 25,
    geographic_scope: 'city',
    agency_name: '',
    client_email: '',
    known_competitors: '',
    has_gbp: false,
    gbp_review_count: 0,
    launch_status: 'live',
    notes: '',
  })

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 700)
    return () => clearTimeout(timer)
  }, [])

  const update = (field: keyof IntakeFormData, value: string | number | boolean) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const canProceed = () => {
    if (step === 1) return form.business_name && form.url && form.industry
    if (step === 2) return form.primary_city
    return true
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      // In production, call the API
      // const result = await apiClient.createClient({
      //   ...form,
      //   neighborhoods: form.neighborhoods.split(',').map(s => s.trim()).filter(Boolean),
      //   known_competitors: form.known_competitors.split('\n').map(s => s.trim()).filter(Boolean),
      // })
      // setResult(result)

      // Simulate response
      setTimeout(() => {
        setResult({
          client_id: 'client-demo1234',
          classification: {
            classification: form.geographic_scope === 'city' ? 'B2C Local' : 'B2C Regional',
            business_type: 'b2c',
            geographic_scope: form.geographic_scope,
            signals: [
              `City-level scope (${form.primary_city})`,
              `${form.neighborhoods ? 'Neighborhoods identified: ' + form.neighborhoods : 'No neighborhoods specified - will discover during recon'}`,
              'Classified as B2C local service business',
              form.has_gbp ? 'Google Business Profile detected' : 'No GBP - will recommend setup',
            ],
            location_page_strategy: form.neighborhoods
              ? `Neighborhood pages for: ${form.neighborhoods}`
              : 'City page + suburb discovery during recon',
            keyword_tier_strategy: 'City + neighborhood long-tail keywords',
          },
          seo_strategy: {
            keyword_tiers: [
              { tier: 1, name: 'Core Local', examples: [`${form.industry} ${form.primary_city}`, `best ${form.industry} ${form.primary_city}`] },
              { tier: 2, name: 'Neighborhood', examples: form.neighborhoods.split(',').slice(0, 3).map(h => `${form.industry} ${h.trim()}`) },
              { tier: 3, name: 'Long-Tail', examples: [`${form.industry} cost ${form.primary_city}`, `emergency ${form.industry} ${form.primary_city}`] },
            ],
            content_priorities: [
              { priority: 1, action: 'Ensure service pages exist for each core service' },
              { priority: 2, action: `Build location pages for ${form.primary_city}` },
              ...(form.has_gbp ? [] : [{ priority: 3, action: 'Set up and optimize Google Business Profile' }]),
              { priority: 4, action: 'Add testimonials with customer locations' },
            ],
            technical_priorities: [
              'Add LocalBusiness JSON-LD schema to homepage',
              'Ensure mobile viewport meta tag is present',
              'Create and submit XML sitemap',
              'Set up Google Search Console',
            ],
          },
        })
        setSubmitting(false)
      }, 1500)
    } catch {
      setSubmitting(false)
    }
  }

  if (loading) return <ClientIntakeSkeleton />

  // ─── Result View ───────────────────────────────────────────────
  if (result) {
    return (
      <div className="page-container" style={{ maxWidth: 800, margin: '0 auto' }}>
        <div style={{ marginBottom: 'var(--space-8)' }} className="animate-in">
          <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
            Client Created
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
            {result.client_id} - Business classified as <strong style={{ color: 'var(--accent-primary)' }}>{result.classification.classification}</strong>
          </p>
        </div>

        {/* Classification */}
        <div className="card animate-in animate-in-delay-1" style={{ marginBottom: 'var(--space-6)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-4)' }}>
            <span style={{ color: 'var(--accent-primary)' }}><Check size={14} weight="bold" /></span>
            <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              BUSINESS CLASSIFICATION
            </h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
            <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Type</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{result.classification.business_type.toUpperCase()}</div>
            </div>
            <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Scope</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{result.classification.geographic_scope}</div>
            </div>
          </div>

          <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Signals</div>
          <div className="stagger-children">
            {result.classification.signals.map((signal, i) => (
              <div key={i} className="stagger-child" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0' }}>
                <span className="status-dot status-dot-live" style={{ flexShrink: 0 }} />
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{signal}</span>
              </div>
            ))}
          </div>
        </div>

        {/* SEO Strategy */}
        <div className="card animate-in animate-in-delay-2" style={{ marginBottom: 'var(--space-6)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-4)' }}>
            <span style={{ color: 'var(--accent-primary)' }}><Lightning size={14} weight="regular" /></span>
            <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              RECOMMENDED SEO STRATEGY
            </h3>
          </div>

          <div className="stagger-children">
            {result.seo_strategy.keyword_tiers.map(tier => (
              <div key={tier.tier} className="stagger-child" style={{ marginBottom: 'var(--space-3)' }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                  Tier {tier.tier}: {tier.name}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {tier.examples.map((kw, i) => (
                    <span key={i} style={{ padding: '2px 8px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', fontSize: 11, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Content Priorities */}
        <div className="card animate-in animate-in-delay-3" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>
            CONTENT PRIORITIES
          </h3>
          <div className="stagger-children">
            {result.seo_strategy.content_priorities.map(item => (
              <div key={item.priority} className="stagger-child" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: '1px solid var(--border-muted)' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent-primary)', minWidth: 20 }}>{item.priority}</span>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{item.action}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="animate-in animate-in-delay-4" style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button
            onClick={() => navigate('/new-audit')}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <ArrowRight size={14} weight="bold" />
            Start SEO Audit for This Client
          </button>
          <button
            onClick={() => { setResult(null); setStep(1); setForm({ business_name: '', url: '', industry: '', primary_city: '', state: '', neighborhoods: '', service_radius_miles: 25, geographic_scope: 'city', agency_name: '', client_email: '', known_competitors: '', has_gbp: false, gbp_review_count: 0, launch_status: 'live', notes: '' }) }}
            className="btn btn-secondary"
          >
            Add Another Client
          </button>
        </div>
      </div>
    )
  }

  // ─── Form View ─────────────────────────────────────────────────
  return (
    <div className="page-container" style={{ maxWidth: 600, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-8)' }} className="animate-in">
        <h1 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
          Client Intake
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
          Step {step} of 3 - {step === 1 ? 'Business Info' : step === 2 ? 'Location & Scope' : 'Additional Details'}
        </p>
      </div>

      {/* Progress Bar */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 'var(--space-6)' }} className="animate-in animate-in-delay-1">
        {[1, 2, 3].map(s => (
          <div key={s} style={{ flex: 1, height: 3, borderRadius: 2, background: s <= step ? 'var(--accent-primary)' : 'var(--border-primary)', transition: 'background 300ms ease' }} />
        ))}
      </div>

      {/* Step 1: Business Info */}
      {step === 1 && (
        <div className="card animate-in animate-in-delay-2">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
            <span style={{ color: 'var(--accent-primary)' }}><Building size={14} weight="regular" /></span>
            <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              BUSINESS INFORMATION
            </h3>
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={labelStyle}>BUSINESS NAME *</label>
            <input value={form.business_name} onChange={e => update('business_name', e.target.value)} placeholder="Acme Plumbing" className="form-input" />
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={labelStyle}>WEBSITE URL *</label>
            <input value={form.url} onChange={e => update('url', e.target.value)} placeholder="https://example.com" className="form-input form-input-mono" />
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={labelStyle}>INDUSTRY / SERVICE *</label>
            <select value={form.industry} onChange={e => update('industry', e.target.value)} className="form-input">
              <option value="">Select industry...</option>
              {INDUSTRIES.map(ind => <option key={ind} value={ind.toLowerCase()}>{ind}</option>)}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
            <div>
              <label style={labelStyle}>AGENCY NAME</label>
              <input value={form.agency_name} onChange={e => update('agency_name', e.target.value)} placeholder="Your agency" className="form-input" />
            </div>
            <div>
              <label style={labelStyle}>CLIENT EMAIL</label>
              <input value={form.client_email} onChange={e => update('client_email', e.target.value)} placeholder="client@example.com" className="form-input" />
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Location & Scope */}
      {step === 2 && (
        <div className="card animate-in animate-in-delay-2">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
            <span style={{ color: 'var(--accent-primary)' }}><MapPin size={14} weight="regular" /></span>
            <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              LOCATION & GEOGRAPHIC SCOPE
            </h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
            <div>
              <label style={labelStyle}>PRIMARY CITY *</label>
              <input value={form.primary_city} onChange={e => update('primary_city', e.target.value)} placeholder="Austin" className="form-input" />
            </div>
            <div>
              <label style={labelStyle}>STATE</label>
              <input value={form.state} onChange={e => update('state', e.target.value)} placeholder="TX" className="form-input" />
            </div>
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={labelStyle}>NEIGHBORHOODS / DISTRICTS</label>
            <input value={form.neighborhoods} onChange={e => update('neighborhoods', e.target.value)} placeholder="Downtown, East Austin, South Austin (comma-separated)" className="form-input" />
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>These become Tier 2 keyword targets and location page candidates</div>
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={labelStyle}>GEOGRAPHIC SCOPE</label>
            <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {([
                ['city', 'Single City / Metro', 'B2C Local - neighborhood + suburb pages'],
                ['regional', 'Multi-City / Regional', 'B2C Regional - city pages + neighborhoods'],
                ['multi-state', 'Multi-State / National', 'B2B - one page per major market'],
              ] as const).map(([value, label, desc]) => (
                <label key={value} className="stagger-child card-interactive" style={{
                  display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
                  background: form.geographic_scope === value ? 'var(--accent-muted)' : 'var(--bg-secondary)',
                  border: `1px solid ${form.geographic_scope === value ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
                  borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                }}>
                  <input type="radio" name="scope" checked={form.geographic_scope === value} onChange={() => update('geographic_scope', value)} style={{ accentColor: 'var(--accent-primary)' }} />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{label}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={labelStyle}>SERVICE RADIUS (MILES)</label>
            <input type="number" value={form.service_radius_miles} onChange={e => update('service_radius_miles', parseInt(e.target.value) || 0)} className="form-input form-input-mono" />
          </div>
        </div>
      )}

      {/* Step 3: Additional Details */}
      {step === 3 && (
        <div className="card animate-in animate-in-delay-2">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
            <span style={{ color: 'var(--accent-primary)' }}><Globe size={14} weight="regular" /></span>
            <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              ADDITIONAL DETAILS
            </h3>
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={labelStyle}>KNOWN COMPETITORS</label>
            <textarea value={form.known_competitors} onChange={e => update('known_competitors', e.target.value)} placeholder={'https://competitor1.com\nhttps://competitor2.com'} rows={3} className="form-input form-input-mono" style={{ resize: 'vertical', fontSize: 12 }} />
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>One URL per line. Leave empty for auto-discovery.</div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
            <div>
              <label style={labelStyle}>LAUNCH STATUS</label>
              <select value={form.launch_status} onChange={e => update('launch_status', e.target.value)} className="form-input">
                <option value="live">Live - current site</option>
                <option value="pre-launch">Pre-launch / Staging</option>
                <option value="rebuild">Rebuild / Redesign</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>GOOGLE BUSINESS PROFILE</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)' }}>
                  <input type="checkbox" checked={form.has_gbp} onChange={e => update('has_gbp', e.target.checked)} style={{ accentColor: 'var(--accent-primary)' }} />
                  Has GBP
                </label>
                {form.has_gbp && (
                  <input type="number" value={form.gbp_review_count} onChange={e => update('gbp_review_count', parseInt(e.target.value) || 0)} placeholder="Reviews" className="form-input form-input-mono" style={{ width: 100 }} />
                )}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={labelStyle}>NOTES</label>
            <textarea value={form.notes} onChange={e => update('notes', e.target.value)} placeholder="Any additional context about this client..." rows={3} className="form-input" style={{ resize: 'vertical' }} />
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="animate-in animate-in-delay-3" style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-6)' }}>
        {step > 1 ? (
          <button onClick={() => setStep(step - 1)} className="btn btn-secondary">Back</button>
        ) : <div />}
        {step < 3 ? (
          <button onClick={() => setStep(step + 1)} disabled={!canProceed()} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6, opacity: canProceed() ? 1 : 0.5 }}>
            Next <ArrowRight size={14} weight="bold" />
          </button>
        ) : (
          <button onClick={handleSubmit} disabled={submitting} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6, opacity: submitting ? 0.6 : 1 }}>
            {submitting ? (
              <>
                <div className="spinner" />
                Classifying...
              </>
            ) : (
              <>
                <UserPlus size={14} weight="regular" />
                Create Client & Classify
              </>
            )}
          </button>
        )}
      </div>

      
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em',
}
