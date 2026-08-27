# CloudGuard DR — Project Brain

> Single source of truth for the current state of the project. Updated in real-time with every change.

---

## Frontend

### Framework & Libraries
- **React 18** with TypeScript, lazy-loaded pages via `React.lazy` + `Suspense`
- **React Router v7** for client-side routing
- **Vite** as bundler (code splitting: `vendor-react`, `vendor-router`, `vendor-icons`, `vendor-http`)
- **Axios** for HTTP requests (interceptor adds Cognito JWT from `localStorage`)
- **Phosphor Icons** (`@phosphor-icons/react`) for icons
- **Geist + Geist Mono** (self-hosted variable fonts via `@font-face`)
- **Husky + lint-staged** for pre-commit linting

### Folder Structure
```
frontend/
├── public/            # sw.js, manifest.json (PWA basics)
├── src/
│   ├── components/
│   │   ├── Layout/    # Navbar.tsx, Footer.tsx
│   │   ├── shared/    # StatusBadge.tsx
│   │   └── ...        # Dashboard, RunDetail, Comparison, NewAudit, Settings subdirs
│   ├── contexts/      # ThemeContext.tsx (dark/light toggle)
│   ├── hooks/         # (empty)
│   ├── pages/         # LandingPage, Dashboard, Runs, RunDetail, Compare, NewAudit, Settings, ClientIntake
│   ├── styles/        # variables.css (design tokens), globals.css, components.css, landing.css
│   ├── utils/         # api.ts (API client + types), format.ts (time/score formatters)
│   ├── App.tsx        # Router + lazy page loading
│   └── main.tsx       # Entry point
```

### Routing
| Path | Component | Purpose |
|------|-----------|---------|
| `/` | LandingPage | Marketing landing page (light theme, no app chrome) |
| `/app` | Dashboard | Overview with summary cards, recent runs |
| `/runs` | Runs | List of all test runs |
| `/runs/:runId` | RunDetail | Single run detail with metrics, timeline, PDF link |
| `/compare` | Compare | Side-by-side comparison of two runs |
| `/new-audit` | NewAudit | Trigger a new DR test or SEO/competitor audit |
| `/settings` | Settings | App configuration |
| `/clients` | ClientIntake | Client onboarding form |
| `*` | NotFound | 404 catch-all page |

### Landing Page
- `LandingPage.tsx` - premium B2B SaaS marketing page (light theme)
- `landing.css` - dedicated styles for landing page
- Landing page has its own nav (inside component), no app Navbar/Footer
- Dashboard moved from `/` to `/app`

### State Management
- No global state library — each page manages its own state via `useState`/`useEffect`
- `ThemeContext` provides dark/light mode via `data-theme` attribute
- Auth token stored in `localStorage.cloudguard_token`, injected by Axios interceptor

### Styling Approach
- CSS custom properties (design tokens) in `variables.css` — dark-first with functional light theme
- Dark theme default, light theme via `[data-theme="light"]` (properly differentiated surfaces/text)
- No CSS framework — vanilla CSS with BEM-ish naming
- Shared classes: `.card`, `.btn`, `.btn-primary`, `.btn-secondary`, `.page-container`, `.skeleton-*`, `.spinner`
- Animations: `animate-in`, `stagger-children`, `page-transition`
- Fonts: `Geist` (primary), `Geist Mono` (mono) — self-hosted via `@font-face` in `variables.css`
- Global focus ring via `:focus-visible` + `--focus-ring` CSS variable
- Skip-to-content link for keyboard accessibility

---

## Backend

### Framework & Language
- **Python 3.12** Lambda functions
- **Terraform** (>= 1.5) for all infrastructure, modular structure
- **AWS** — serverless-first architecture

### Folder Structure
```
lambdas/
├── api/               # Main API Lambda (runs, compare, report routing)
├── injection/         # Starts FIS experiment (EC2 termination)
├── monitor/           # Polls CloudWatch/ALB/Route53 for recovery
├── measurement/       # Calculates RTO and RPO from timestamps
├── scoring/           # Converts RTO/RPO to 0-100 score, stores in DynamoDB
├── audit-report/      # Generates JSON + HTML report, invokes PDF lambda
├── pdf-report/        # Converts JSON report to branded PDF (weasyprint)
├── external-audit/    # HTTPS/DNS/response-time health checks
├── seo-report/        # SEO audit of a URL
├── competitor-analysis/ # Competitive analysis
├── client-intake/     # Client onboarding and classification
└── alert/             # Sends SNS alerts

terraform/
├── main.tf            # Root module wiring
├── environments/      # dev/, demo/ environment configs
└── modules/           # iam, lambda, dynamodb, s3, cognito, api-gateway,
                        # step-functions, fis, eventbridge, cloudwatch,
                        # sns, ssm, network, sample-app
```

### API Endpoints
| Method | Path | Lambda | Auth | Purpose |
|--------|------|--------|------|---------|
| GET | `/runs` | api | Cognito JWT | List test runs |
| GET | `/runs/{runId}` | api | Cognito JWT | Get single run |
| GET | `/runs/{runId}/report` | api | Cognito JWT | Get audit report for a run |
| POST | `/compare` | api | Cognito JWT | Compare two runs |
| POST | `/audit/external` | external-audit | Cognito JWT | Run external health audit |
| POST | `/audit/seo` | seo-report | Cognito JWT | Run SEO audit |
| POST | `/audit/competitors` | competitor-analysis | Cognito JWT | Run competitor analysis |
| POST | `/report/pdf` | pdf-report | Cognito JWT | Generate PDF from JSON report |
| GET | `/clients` | client-intake | Cognito JWT | List clients |
| POST | `/clients` | client-intake | Cognito JWT | Create client |
| GET | `/clients/{clientId}` | client-intake | Cognito JWT | Get client |
| GET | `/health` | api | None | Health check |

### Database Schema (DynamoDB)

**`cloudguard-{env}-test-runs`** — hash: `run_id`
- `run_id`, `timestamp`, `fault_type`, `target_resource`
- `rto_seconds`, `rpo_seconds`, `resilience_score`, `status`
- `rto_target`, `rpo_target`, `report_s3_key`
- `stage_timestamps` (map: inject, recover)
- GSI: `timestamp-index` (hash: `timestamp`, range: `run_id`)

**`cloudguard-{env}-audit-reports`** — hash: `report_id`
- `report_id`, `run_id`, `target_url`
- `https_valid`, `dns_failover_ok`, `response_time_ms`, `http_status_code`, `ssl_expiry_days`
- `generated_at`, `fault_type`, `rto_seconds`, `rpo_seconds`, `resilience_score`
- `s3_report_key`
- GSI: `run_id-index` (hash: `run_id`)

**`cloudguard-{env}-clients`** — hash: `client_id`
- `client_id`, `created_at`, `business_name`, `url`, `industry`
- `primary_city`, `state`, `neighborhoods`, `service_radius_miles`
- `geographic_scope`, `business_type`, `classification` (map)
- `seo_strategy` (map), `agency_name`, `client_email`
- `known_competitors`, `has_gbp`, `gbp_review_count`, `launch_status`
- GSI: `created_at-index` (hash: `created_at`)

### Auth
- **AWS Cognito User Pools** — email-based signup/login
- SRP auth flow, JWT tokens (1hr access/id, 30d refresh)
- API Gateway validates JWT via Cognito authorizer on all endpoints except `/health`
- Frontend stores token in `localStorage`, Axios interceptor attaches it

### Key Business Logic Locations
- **RTO/RPO calculation**: `lambdas/measurement/handler.py` — `calculate_rto()`, `calculate_rpo()`
- **Resilience scoring**: `lambdas/scoring/handler.py` — `calculate_score()` (60% RTO, 40% RPO weighting)
- **Recovery monitoring**: `lambdas/monitor/handler.py` — `check_alb_health()`, `check_instance_recovery()`, `check_route53_health()`
- **PDF generation**: `lambdas/pdf-report/handler.py` — HTML templates for SEO, competitor, DR-test reports
- **Client classification**: `lambdas/client-intake/handler.py`

---

## System Design

### Architecture Overview
```
Browser → CloudFront → S3 (static SPA)
Browser → API Gateway → Lambda (per-route)
                     ↘ Cognito (JWT auth)

Step Function Pipeline:
  EventBridge (weekly cron) → Inject → Monitor → Measure → Score → Audit Report → (async) PDF → Alert

Data Stores:
  DynamoDB (runs, reports, clients) | S3 (JSON/HTML/PDF reports, static assets) | SSM (config params)
```

### Data Flow — DR Test Run
1. **Trigger**: EventBridge fires weekly (Monday 8AM UTC) or manual via `/new-audit`
2. **Inject**: Injection Lambda starts FIS experiment to terminate tagged EC2 instance
3. **Monitor**: Monitor Lambda polls ALB/EC2/Route53 every 15s (max 10min) until recovery or timeout
4. **Measure**: Measurement Lambda calculates RTO (injection→recovery delta + 5s buffer) and RPO
5. **Score**: Scoring Lambda computes 0-100 score (RTO weighted 60%, RPO 40%), stores in DynamoDB
6. **Report**: Audit Report Lambda generates JSON + HTML to S3, stores pointer in DynamoDB, invokes PDF Lambda async
7. **PDF**: PDF Lambda (async, non-blocking) converts JSON to branded PDF via weasyprint, stores in S3
8. **Alert**: Alert Lambda sends SNS notification with score/status

### Data Flow — Frontend
1. User navigates to `/runs/:runId`
2. `RunDetail` fetches run data via `GET /runs/{runId}` and report via `GET /runs/{runId}/report` in parallel
3. If report has `pdf_url`, shows "Download PDF" link; otherwise shows "Generate PDF Report" button
4. Manual PDF generation calls `POST /report/pdf` → pdf-report Lambda

### External Services
- **AWS FIS** — Fault Injection Simulator (EC2 termination experiments)
- **AWS Cognito** — User authentication
- **AWS SNS** — Alert notifications (email)
- **weasyprint** — HTML-to-PDF conversion (Lambda layer, optional — falls back to HTML)
- **CloudWatch** — Monitoring metrics and alarms
- **Route 53** — DNS health checks

### Deployment
- **Terraform** manages all AWS infrastructure (modular, `terraform/environments/{dev,demo}`)
- **Frontend**: Vite build → S3 static hosting (dashboard bucket with public read)
- **Backend**: Lambda functions packaged as zip files via `archive_file` data source
- **PDF layer**: Manual build required — `lambdas/pdf-report/LAYER_BUILD.md` has instructions
- **Environments**: `dev` (default), `demo`
- Remote state: S3 backend configured but commented out (using local state)

### Key Architectural Decisions
| Decision | Reason |
|----------|--------|
| Serverless (Lambda + API Gateway) | Zero ops, auto-scaling, pay-per-use for a tool that runs weekly |
| Step Functions for DR pipeline | Visual workflow, built-in retry/catch, easy to debug failed runs |
| Async PDF generation | weasyprint is slow (~5-10s); async invocation keeps the pipeline fast |
| DynamoDB (PAY_PER_REQUEST) | No capacity planning needed, on-demand fits sporadic usage |
| Modular Terraform | Each service is an isolated module — easy to test, swap, or remove |
| Cognito over custom auth | Managed service, handles SRP/JWT/refresh tokens, no Lambda needed for auth |
| S3 for reports (not DynamoDB) | Reports are large JSON/HTML/PDfs — S3 is cheaper and purpose-built for blobs |
| weasyprint as optional layer | If layer isn't deployed, PDF Lambda falls back to HTML — no hard dependency |
| FIS for fault injection | Native AWS service, integrates with IAM/cloudwatch, safer than manual termination |
