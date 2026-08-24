import axios from 'axios'

// Types
export interface TestRun {
  run_id: string
  timestamp: string
  fault_type: string
  target_resource: string
  rto_seconds: number
  rpo_seconds: number
  resilience_score: number
  status: 'Passed' | 'Failed' | 'Incomplete'
  rto_target: number
  rpo_target: number
  report_s3_key: string
}

export interface AuditReport {
  report_id: string
  run_id: string | null
  target_url: string
  https_valid: boolean
  dns_failover_ok: boolean
  response_time_ms: number | null
  http_status_code: number
  ssl_expiry_days: number | null
  generated_at: string
  fault_type: string | null
  rto_seconds: number | null
  rpo_seconds: number | null
  resilience_score: number | null
}

export interface HealthChecks {
  https_valid: boolean
  dns_failover_ok: boolean
  response_time_ms: number | null
  http_status_code: number
  ssl_expiry_days: number | null
}

export interface SEOReport {
  report_id: string
  target_url: string
  generated_at: string
  page_fetched: boolean
  status_code: number
  response_time_ms: number
  content_length: number
  seo_score: number
  seo_checks: {
    title: SEOCheckItem
    meta_description: SEOCheckItem
    headings: SEOCheckItem & { h1_count: number; has_h1: boolean; has_h2: boolean; hierarchy_valid: boolean }
    images: SEOCheckItem & { total: number; with_alt: number; without_alt: number; all_have_alt: boolean }
    links: SEOCheckItem & { total: number; internal: number; external: number; nofollow: number }
    canonical: SEOCheckItem
    open_graph: SEOCheckItem & { tags_found: string[]; tags_missing: string[] }
    twitter_card: SEOCheckItem & { tags_found: string[]; tags_missing: string[] }
    viewport: SEOCheckItem
    robots: SEOCheckItem
    structured_data: SEOCheckItem & { types: string[]; count: number }
    performance: SEOCheckItem & { response_time_ms: number; fast: boolean; content_size_kb: number }
    https: SEOCheckItem
  }
}

export interface SEOCheckItem {
  present?: boolean
  issues: string[]
  value?: string | null
  [key: string]: unknown
}

export interface CompetitorAnalysis {
  analysis_id: string
  target_url: string
  industry: string
  city: string
  geographic_scope: string
  competitor_count: number
  generated_at: string
  site_analyses: Record<string, SiteAnalysis>
  feature_matrix: Record<string, Record<string, unknown>>
  gap_analysis: GapAnalysis
  strategic_opportunities: StrategicOpportunity[]
}

export interface SiteAnalysis {
  url: string
  domain: string
  status_code: number
  response_time_ms: number
  content_length: number
  https_valid: boolean
  title: string
  title_length: number
  meta_description: string
  meta_desc_length: number
  has_viewport: boolean
  canonical: boolean
  has_og_tags: boolean
  og_tag_count: number
  has_twitter_tags: boolean
  h1_count: number
  has_h1: boolean
  has_h2: boolean
  has_blog: boolean
  has_pricing: boolean
  has_testimonials: boolean
  has_schema: boolean
  schema_types: string[]
  schema_count: number
  alt_text_ratio: number
  total_images: number
  total_links: number
  cta_count: number
  has_phone: boolean
  nav_link_count: number
}

export interface GapAnalysis {
  client_score: number
  competitor_scores: Record<string, number>
  average_competitor_score: number
  max_competitor_score: number
  min_competitor_score: number
  client_rank: number
  total_sites: number
  feature_gaps: FeatureGap[]
  content_gaps: ContentGap[]
}

export interface FeatureGap {
  feature: string
  client_has: boolean
  competitors_with: number
  competitor_pct: number
  severity: 'critical' | 'important' | 'minor'
}

export interface ContentGap {
  gap: string
  impact: string
  detail: string
}

export interface StrategicOpportunity {
  title: string
  description: string
  impact: string
  effort: string
  details: Array<{ action: string; feature?: string; competitor_adoption?: string }>
}

export interface ClientIntake {
  client_id: string
  created_at: string
  business_name: string
  url: string
  industry: string
  primary_city: string
  state: string
  neighborhoods: string[]
  service_radius_miles: number
  geographic_scope: 'city' | 'regional' | 'multi-state'
  business_type: 'b2c' | 'b2b'
  classification: BusinessClassification
  seo_strategy: SEOStrategy
  agency_name: string
  client_email: string
  known_competitors: string[]
  has_gbp: boolean
  gbp_review_count: number
  launch_status: string
  old_domain: string | null
  notes: string
}

export interface BusinessClassification {
  business_type: 'b2c' | 'b2b'
  geographic_scope: 'city' | 'regional' | 'multi-state'
  classification: string
  signals: string[]
  location_page_strategy: string
  keyword_tier_strategy: string
}

export interface SEOStrategy {
  keyword_tiers: KeywordTier[]
  content_priorities: ContentPriority[]
  location_page_plan: LocationPage[]
  technical_priorities: string[]
}

export interface KeywordTier {
  tier: number
  name: string
  intent: string
  examples: string[]
  target_page: string
}

export interface ContentPriority {
  priority: number
  action: string
}

export interface LocationPage {
  page: string
  url: string
  keywords: string[]
}

export interface PDFReport {
  statusCode: number
  pdf_key: string
  pdf_url: string
  report_type: string
  report_id: string
  format: 'pdf' | 'html_fallback'
  generated_at?: string
  message?: string
}

export interface ComparisonResult {
  run_a: TestRun
  run_b: TestRun
  deltas: {
    score: DeltaValue
    rto: DeltaValue
    rpo: DeltaValue
  }
  reports: {
    a: AuditReport | null
    b: AuditReport | null
  }
  warning: string | null
}

export interface DeltaValue {
  value_a: number
  value_b: number
  delta: number
  improved: boolean
}

// API client
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://api.cloudguard.example.com/prod',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cloudguard_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// API functions
export const apiClient = {
  // Runs
  async getRuns(params?: { status?: string; fault_type?: string; limit?: number }) {
    const response = await api.get<{ runs: TestRun[]; count: number }>('/runs', { params })
    return response.data
  },

  async getRun(runId: string) {
    const response = await api.get<TestRun>(`/runs/${runId}`)
    return response.data
  },

  async getRunReport(runId: string) {
    const response = await api.get(`/runs/${runId}/report`)
    return response.data
  },

  // Compare
  async compareRuns(runIdA: string, runIdB: string) {
    const response = await api.post<ComparisonResult>('/compare', {
      run_id_a: runIdA,
      run_id_b: runIdB,
    })
    return response.data
  },

  // External audit
  async runExternalAudit(targetUrl: string) {
    const response = await api.post('/audit/external', { target_url: targetUrl })
    return response.data
  },

  // SEO audit
  async runSEOAudit(targetUrl: string) {
    const response = await api.post<SEOReport>('/audit/seo', { target_url: targetUrl })
    return response.data
  },

  // Competitor analysis
  async runCompetitorAnalysis(params: {
    target_url: string
    industry?: string
    city?: string
    geographic_scope?: string
    competitor_urls?: string[]
  }) {
    const response = await api.post<CompetitorAnalysis>('/audit/competitors', params)
    return response.data
  },

  // Client intake
  async createClient(data: {
    business_name: string
    url: string
    industry: string
    primary_city: string
    state?: string
    neighborhoods?: string[]
    service_radius_miles?: number
    geographic_scope?: string
    agency_name?: string
    client_email?: string
    known_competitors?: string[]
    has_gbp?: boolean
    gbp_review_count?: number
    launch_status?: string
    notes?: string
  }) {
    const response = await api.post<{ client_id: string; classification: BusinessClassification; seo_strategy: SEOStrategy }>('/clients', data)
    return response.data
  },

  async getClients() {
    const response = await api.get<{ clients: ClientIntake[]; count: number }>('/clients')
    return response.data
  },

  async getClient(clientId: string) {
    const response = await api.get<ClientIntake>(`/clients/${clientId}`)
    return response.data
  },

  // PDF report generation
  async generatePDFReport(params: {
    report_type: 'seo' | 'competitor' | 'dr-test'
    report_id: string
    agency_name?: string
  }) {
    const response = await api.post<PDFReport>('/report/pdf', params)
    return response.data
  },

  // Health check
  async healthCheck() {
    const response = await api.get('/health')
    return response.data
  },
}
