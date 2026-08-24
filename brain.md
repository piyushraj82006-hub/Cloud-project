# CloudGuard DR — Project Brain

> **This file is the single source of truth for the CloudGuard DR project.**
> Any AI agent reading this file should be able to understand the full project context, architecture, and current state without reading any other files.

---

## 1. Project Overview

**CloudGuard DR** is an automated disaster recovery testing, resilience scoring, and site audit comparison platform built on AWS. It proves your DR works by actually breaking the system on a schedule, not by assumption.

### Core Capabilities

| Capability | Status | Lambda |
|-----------|--------|--------|
| DR Fault Injection Testing | ✅ Implemented | `injection`, `monitor`, `measurement`, `scoring` |
| Audit Report Generation | ✅ Implemented | `audit-report` |
| External Site Health Audit | ✅ Implemented | `external-audit` |
| SEO Audit Report | ✅ Implemented | `seo-report` |
| Competitive Analysis | ✅ Implemented | `competitor-analysis` (with auto-discovery) |
| PDF Report Generation | ✅ Implemented | `pdf-report` |
| Client Intake & Classification | ✅ Implemented | `client-intake` |
| API Gateway (REST) | ✅ Implemented | `api` |
| Alerting (SNS) | ✅ Implemented | `alert` |
| React Dashboard | ✅ Implemented | `frontend/` |

### Tech Stack

| Layer | Choice |
|-------|--------|
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Backend | AWS Lambda (Python 3.12) |
| Orchestration | AWS Step Functions |
| Fault Injection | AWS FIS |
| Database | Amazon DynamoDB (on-demand) |
| Storage | Amazon S3 |
| API | Amazon API Gateway (REST, Cognito-auth) |
| Frontend | React 18 + TypeScript + Vite |
| Auth | Amazon Cognito |
| Alerting | Amazon SNS |
| PDF Generation | weasyprint (Lambda layer) |

---

## 2. Architecture

```
EventBridge / Manual trigger
        │
        ▼
Step Functions ──► Injection Lambda ──► AWS FIS (breaks target)
        │
        ▼
   Monitor Lambda ──► CloudWatch + Route 53
        │
        ▼
 Measurement Lambda ──► RTO/RPO calculation
        │
        ▼
   Scoring Lambda ──► DynamoDB (TestRun record)
        │
        ▼
Audit Report Lambda ──► S3 (report) + DynamoDB (pointer)
        │
        ▼
   Alert Lambda ──► SNS (if score below threshold)

API Gateway ──► React Dashboard
    ├── GET  /runs                  → api (list runs)
    ├── GET  /runs/{run_id}         → api (get run)
    ├── GET  /runs/{run_id}/report  → api (get report)
    ├── POST /compare               → api (compare runs)
    ├── POST /audit/external        → external-audit
    ├── POST /audit/seo             → seo-report
    ├── POST /audit/competitors     → competitor-analysis
    ├── POST /report/pdf            → pdf-report
    ├── GET/POST /clients           → client-intake
    ├── GET  /clients/{client_id}   → client-intake
    └── GET  /health                → api (no auth)
```

---

## 3. All Lambdas — Detailed

### 3.1 `injection` — FIS Experiment Trigger
- **Purpose**: Starts an AWS FIS experiment to terminate tagged EC2 instances
- **Trigger**: Step Functions
- **Input**: `{"fault_type": "ec2-termination", "target_resource": "auto"}`
- **Output**: `{"experiment_id": "...", "status": "running"}`
- **AWS Services**: FIS, EC2

### 3.2 `monitor` — Recovery Monitoring
- **Purpose**: Monitors CloudWatch metrics and Route 53 health checks during/after injection
- **Trigger**: Step Functions (after injection)
- **Timeout**: 900s (15 min) — waits for recovery
- **AWS Services**: CloudWatch, Route 53, EC2

### 3.3 `measurement` — RTO/RPO Calculation
- **Purpose**: Calculates actual Recovery Time Objective and Recovery Point Objective
- **Trigger**: Step Functions (after monitoring)
- **AWS Services**: CloudWatch, DynamoDB

### 3.4 `scoring` — Resilience Score
- **Purpose**: Converts RTO/RPO into a single 0-100 resilience score
- **Trigger**: Step Functions (after measurement)
- **AWS Services**: DynamoDB, SSM Parameter Store
- **Output**: `{"run_id": "...", "resilience_score": 82, "status": "Passed"}`

### 3.5 `audit-report` — DR Audit Report
- **Purpose**: Generates structured audit report with resilience data + site health checks
- **Trigger**: Step Functions (after scoring)
- **Output**: JSON + HTML reports to S3, pointer in DynamoDB
- **Health Checks**: HTTPS validity, DNS failover, response time, SSL expiry, HTTP status
- **AWS Services**: S3, DynamoDB

### 3.6 `external-audit` — External Site Health Audit
- **Purpose**: Non-intrusive health checks on arbitrary external URLs (no fault injection)
- **Trigger**: API Gateway `POST /audit/external`
- **Input**: `{"target_url": "https://example.com"}`
- **Checks**: HTTPS, DNS resolution, response time, content length, SSL
- **AWS Services**: S3, DynamoDB

### 3.7 `seo-report` — SEO Audit Report
- **Purpose**: Comprehensive SEO analysis of a target URL
- **Trigger**: API Gateway `POST /audit/seo`
- **Input**: `{"target_url": "https://example.com"}`
- **Analysis**:
  - Meta tags (title length, description length)
  - Heading structure (H1 count, hierarchy)
  - Images (alt text presence)
  - Links (internal/external/nofollow, broken links)
  - Canonical URL
  - Open Graph / Twitter Card tags
  - Viewport (mobile)
  - Robots / indexing
  - Structured data (JSON-LD)
  - Performance (response time, page size)
  - HTTPS / SSL
- **Scoring**: 0-100 overall SEO score based on weighted checks
- **Output**: JSON + HTML reports to S3, pointer in DynamoDB
- **AWS Services**: S3, DynamoDB

### 3.8 `competitor-analysis` — Competitive Analysis
- **Purpose**: Finds and analyzes 6-8 competitors, builds feature matrix, generates strategic opportunities
- **Trigger**: API Gateway `POST /audit/competitors`
- **Input**:
  ```json
  {
    "target_url": "https://example.com",
    "industry": "plumbing",
    "city": "Austin",
    "geographic_scope": "city",
    "competitor_urls": []  // optional — auto-discovers if empty
  }
  ```
- **Auto-Discovery**: Uses DuckDuckGo HTML search to find competitors based on industry + city (no API key needed)
- **Analysis per site**: Title, meta desc, H1/H2, blog, pricing, testimonials, schema, OG tags, Twitter tags, alt text ratio, response time, phone numbers
- **Outputs**:
  - Feature matrix (side-by-side comparison)
  - Gap analysis (critical/important/minor feature gaps)
  - Competitive scoring (0-100 per site, client ranking)
  - Top 3 strategic opportunities (grounded in actual competitive gaps)
- **AWS Services**: S3, DynamoDB

### 3.9 `pdf-report` — PDF Report Generator
- **Purpose**: Generates branded PDF reports from existing JSON audit data
- **Trigger**: API Gateway `POST /report/pdf`
- **Input**:
  ```json
  {
    "report_type": "seo" | "competitor" | "dr-test",
    "report_id": "seo-abc12345",
    "agency_name": "Acme Agency"  // optional
  }
  ```
- **PDF Features**:
  - Branded cover page (dark gradient, CloudGuard DR logo, green accent)
  - Table of contents
  - Executive summary with stat cards (color-coded green/amber/red)
  - Detailed audit sections with PASS/FAIL badges
  - Print-optimized CSS (@page rules, page breaks, footers)
- **Fallback**: If weasyprint layer not installed, returns print-optimized HTML
- **Dependency**: weasyprint (Lambda layer — see `lambdas/pdf-report/LAYER_BUILD.md`)
- **AWS Services**: S3

### 3.10 `client-intake` — Client Intake & Classification
- **Purpose**: Accepts business info, classifies B2C/B2B, generates SEO strategy
- **Trigger**: API Gateway `GET/POST /clients`, `GET /clients/{client_id}`
- **Input**:
  ```json
  {
    "business_name": "Acme Plumbing",
    "url": "https://acmeplumbing.com",
    "industry": "plumbing",
    "primary_city": "Austin",
    "state": "TX",
    "neighborhoods": ["Downtown", "East Austin"],
    "service_radius_miles": 25,
    "geographic_scope": "city",
    "agency_name": "Growth Agency",
    "client_email": "client@example.com",
    "known_competitors": [],
    "has_gbp": true,
    "gbp_review_count": 127,
    "launch_status": "live",
    "notes": "Fast-growing local plumbing company"
  }
  ```
- **Classification Logic**:
  - **B2C Local**: Single city, consumer-facing → neighborhood + suburb pages
  - **B2C Regional**: Multi-city, one state → city pages + neighborhoods
  - **B2B Multi-State**: Multi-region, contract-based → one page per major market
- **Strategy Output**:
  - 4 keyword tiers (Core Local → Neighborhood → Long-Tail → Informational)
  - Content priorities ranked by impact
  - Location page plan based on neighborhoods
  - Technical SEO priorities
- **AWS Services**: DynamoDB

### 3.11 `api` — API Gateway Handler
- **Purpose**: Handles all REST API requests for runs, reports, and comparisons
- **Trigger**: API Gateway (all routes except audit/*, report/*, clients/*)
- **Routes**: GET /runs, GET /runs/{id}, GET /runs/{id}/report, POST /compare, GET /health
- **AWS Services**: DynamoDB, S3

### 3.12 `alert` — SNS Alerting
- **Purpose**: Sends email alerts when resilience score falls below threshold
- **Trigger**: Step Functions (after scoring, if score < threshold)
- **AWS Services**: SNS, DynamoDB, SSM Parameter Store

---

## 4. DynamoDB Tables

| Table | Partition Key | GSI | Purpose |
|-------|--------------|-----|---------|
| `cloudguard-{env}-test-runs` | `run_id` (S) | `timestamp-index` on `timestamp` | DR test run records |
| `cloudguard-{env}-audit-reports` | `report_id` (S) | `run_id-index` on `run_id` | Audit report pointers (SEO, DR, competitor) |
| `cloudguard-{env}-clients` | `client_id` (S) | `created_at-index` on `created_at` | Client intake records with classification |

---

## 5. S3 Buckets

| Bucket | Purpose | Access |
|--------|---------|--------|
| `cloudguard-reports-{account_id}` | Audit reports (JSON/HTML/PDF) | Lambda write, API read |
| `cloudguard-dashboard-{account_id}` | React dashboard static files | Public read |

### S3 Key Structure
```
reports/{run_id}/report.json          — DR audit report
reports/{run_id}/report.html         — DR audit report (HTML)
seo-reports/{report_id}/report.json   — SEO audit report
seo-reports/{report_id}/report.html   — SEO audit report (HTML)
competitor-analysis/{id}/report.json  — Competitor analysis
competitor-analysis/{id}/report.html  — Competitor analysis (HTML)
external-audits/{id}/report.json      — External site audit
pdf-reports/{id}/report.pdf           — Generated PDF reports
pdf-reports/{id}/report.html          — PDF fallback (HTML)
```

---

## 6. API Gateway Endpoints

| Method | Path | Lambda | Auth |
|--------|------|--------|------|
| GET | `/runs` | api | Cognito JWT |
| GET | `/runs/{run_id}` | api | Cognito JWT |
| GET | `/runs/{run_id}/report` | api | Cognito JWT |
| POST | `/compare` | api | Cognito JWT |
| POST | `/audit/external` | external-audit | Cognito JWT |
| POST | `/audit/seo` | seo-report | Cognito JWT |
| POST | `/audit/competitors` | competitor-analysis | Cognito JWT |
| POST | `/report/pdf` | pdf-report | Cognito JWT |
| GET | `/clients` | client-intake | Cognito JWT |
| POST | `/clients` | client-intake | Cognito JWT |
| GET | `/clients/{client_id}` | client-intake | Cognito JWT |
| GET | `/health` | api | None |

---

## 7. Terraform Modules

| Module | Purpose |
|--------|---------|
| `network` | VPC, subnets, internet gateway |
| `iam` | IAM roles for all lambdas + Step Functions + FIS + EventBridge |
| `dynamodb` | DynamoDB tables (test-runs, audit-reports, clients) |
| `s3` | S3 buckets (reports, dashboard) |
| `cognito` | Cognito user pool + app client |
| `sns` | SNS topic for alerts |
| `fis` | FIS experiment template |
| `step-functions` | Step Functions state machine |
| `sample-app` | Sample EC2 app (system under test) |
| `lambda` | All Lambda functions |
| `api-gateway` | REST API + all endpoints |
| `ssm` | SSM Parameter Store (RTO/RPO targets, thresholds) |
| `eventbridge` | Scheduled test triggers |
| `cloudwatch` | Log groups + failure alarms |

---

## 8. Frontend

### Pages

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/` | Score trends, recent runs, alerts |
| Runs | `/runs` | List all DR test runs |
| RunDetail | `/runs/:runId` | Single run detail + Generate PDF button |
| Compare | `/compare` | Side-by-side run comparison |
| NewAudit | `/new-audit` | Start DR test, external audit, SEO audit, or competitor analysis |
| ClientIntake | `/clients` | 3-step client intake form with business classification |
| Settings | `/settings` | RTO/RPO thresholds, alert config, schedule |

### Key Components

- `Navbar` — Top navigation
- `Footer` — Bottom footer
- `StatusBadge` — Passed/Failed/Incomplete badge
- `Layout/` — Layout components

### API Client (`frontend/src/utils/api.ts`)

Types exported: `TestRun`, `AuditReport`, `HealthChecks`, `SEOReport`, `SEOCheckItem`, `CompetitorAnalysis`, `SiteAnalysis`, `GapAnalysis`, `FeatureGap`, `ContentGap`, `StrategicOpportunity`, `PDFReport`, `ClientIntake`, `BusinessClassification`, `SEOStrategy`, `KeywordTier`, `ContentPriority`, `LocationPage`, `ComparisonResult`, `DeltaValue`

---

## 9. Environment Variables

All lambdas use these patterns:
```
ENVIRONMENT           = dev | demo
AWS_REGION            = us-east-1
REPORTS_BUCKET        = cloudguard-{env}-reports
AUDIT_REPORTS_TABLE   = cloudguard-{env}-audit-reports
CLIENTS_TABLE         = cloudguard-{env}-clients
TEST_RUNS_TABLE       = cloudguard-{env}-test-runs
SNS_TOPIC_ARN         = arn:aws:sns:...
```

---

## 10. Cost Estimate

| Service | Free Tier | Estimated Monthly |
|---------|-----------|-------------------|
| Lambda | 1M requests | $0 |
| DynamoDB | 25 GB, 25 WCU/RCU | $0 |
| S3 | 5 GB | $0 |
| Step Functions | 4K transitions | $0 |
| FIS | — | ~$0.40 (weekly tests) |
| API Gateway | 1M calls | $0 |
| Cognito | 50K MAUs | $0 |
| SNS | 1M publishes | $0 |
| EC2 (sample app) | 750 hrs | ~$7.50 (2× t3.micro) |
| **Total** | | **~$7.50–$15/month** |

---

## 11. Change Log

### Phase 1: Core DR Platform (Initial)
- ✅ Terraform infrastructure (all modules)
- ✅ DR testing lambdas (injection, monitor, measurement, scoring)
- ✅ Audit report + alert lambdas
- ✅ API Gateway + Cognito auth
- ✅ React dashboard (Dashboard, Runs, RunDetail, Compare, Settings, NewAudit)
- ✅ GitHub Actions CI/CD

### Phase 2: SEO & Competitive Analysis
- ✅ **SEO Report Lambda** — Full SEO analysis (meta, headings, images, links, schema, performance, OG/Twitter tags)
- ✅ **Competitor Analysis Lambda** — Auto-discovers competitors via DuckDuckGo, builds feature matrix, gap analysis, strategic opportunities
- ✅ **Client Intake Lambda** — Business classification (B2C/B2B), SEO strategy generation, DynamoDB storage
- ✅ Frontend: NewAudit page updated with SEO audit + competitor analysis options
- ✅ Frontend: ClientIntake page (3-step form with classification result view)
- ✅ Frontend: API types for all new features

### Phase 3: PDF Reports
- ✅ **PDF Report Lambda** — Branded PDF generation with weasyprint (cover page, executive summary, detailed sections)
- ✅ Lambda layer setup instructions (`lambdas/pdf-report/LAYER_BUILD.md`)
- ✅ Frontend: Generate PDF button on RunDetail page
- ✅ Graceful HTML fallback if weasyprint not available

### Infrastructure Changes Summary
- 12 Lambda functions total
- 3 DynamoDB tables
- 14 API Gateway endpoints
- 14 CloudWatch log groups
- 14 IAM roles
- All wired through Terraform modules

---

## 12. Key Design Decisions

1. **No AI API keys** — All analysis uses Python stdlib (urllib, html.parser) + DuckDuckGo (no key)
2. **Lambda layers for heavy deps** — weasyprint needs a compiled layer, everything else is stdlib
3. **On-demand DynamoDB** — No capacity planning needed, pay per request
4. **Cognito JWT auth** — All API endpoints except /health require authentication
5. **S3 for reports** — JSON + HTML + PDF all stored in S3, pointers in DynamoDB
6. **Auto-competitor discovery** — Uses DuckDuckGo HTML scraping (no API key, no rate limits)
7. **Business classification** — Rule-based (not AI), deterministic, fast

---

## 13. Files Modified/Created in This Session

### New Files
- `lambdas/seo-report/handler.py` — SEO audit Lambda
- `lambdas/competitor-analysis/handler.py` — Competitor analysis Lambda
- `lambdas/pdf-report/handler.py` — PDF report Lambda
- `lambdas/pdf-report/requirements.txt` — weasyprint dependency
- `lambdas/pdf-report/LAYER_BUILD.md` — Lambda layer build instructions
- `lambdas/client-intake/handler.py` — Client intake Lambda
- `frontend/src/pages/ClientIntake.tsx` — Client intake form page
- `brain.md` — This file

### Modified Files
- `terraform/modules/iam/main.tf` — Added roles: seo-report, competitor-analysis, pdf-report, client-intake
- `terraform/modules/lambda/main.tf` — Added functions: seo-report, competitor-analysis, pdf-report, client-intake
- `terraform/modules/api-gateway/main.tf` — Added endpoints: /audit/seo, /audit/competitors, /report/pdf, /clients
- `terraform/modules/dynamodb/main.tf` — Added clients table
- `terraform/modules/cloudwatch/main.tf` — Added log groups for new lambdas
- `terraform/main.tf` — Wired up all new module variables
- `frontend/src/utils/api.ts` — Added types + API methods for all new features
- `frontend/src/pages/NewAudit.tsx` — Added SEO audit + competitor analysis options
- `frontend/src/pages/RunDetail.tsx` — Added Generate PDF button
- `frontend/src/App.tsx` — Added /clients route
