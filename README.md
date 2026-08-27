# CloudGuard DR

**Automated Disaster Recovery Testing, Resilience Scoring & Site Audit Comparison Platform**

---

## Overview

CloudGuard DR proves your disaster recovery works by actually breaking the system on a schedule, not by assumption. It uses AWS Fault Injection Simulator to terminate EC2 instances, measures recovery time and data loss, converts them into a single resilience score, and generates audit reports that can be compared side by side.

## Features

- **Fault Injection Engine** — AWS FIS terminates tagged EC2 instances on schedule
- **Test Orchestration** — Step Functions coordinates: Inject → Monitor → Measure → Score → Report → Alert
- **RTO/RPO Measurement** — Lambda calculates actual recovery time and data loss
- **Resilience Scoring** — Converts RTO/RPO into a single 0–100 score
- **Live Failover Demo** — Route 53 health checks trigger real failover
- **Site Audit & Comparison** — Auto-generated audit reports, side-by-side comparison
- **Dark Technical Dashboard** — React frontend with score trends, reports, and comparison view

## Architecture

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
        │
        ▼
API Gateway ──► React Dashboard
```

## Tech Stack

| Layer | Choice |
|-------|--------|
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Backend | AWS Lambda (Python 3.12) |
| Orchestration | AWS Step Functions |
| Fault Injection | AWS FIS |
| Database | Amazon DynamoDB |
| Storage | Amazon S3 |
| API | Amazon API Gateway |
| Frontend | React + TypeScript + Vite |
| Auth | Amazon Cognito |
| Alerting | Amazon SNS |

## Project Structure

```
cloud/
├── terraform/          # IaC modules
│   ├── modules/        # network, iam, lambda, dynamodb, s3, etc.
│   └── environments/   # dev, demo
├── lambdas/            # Lambda function code
│   ├── injection/      # FIS experiment trigger
│   ├── monitor/        # Recovery monitoring
│   ├── measurement/    # RTO/RPO calculation
│   ├── scoring/        # Resilience score
│   ├── audit-report/   # Report generation
│   ├── external-audit/ # External site audit
│   ├── alert/          # SNS notifications
│   └── api/            # API Gateway handlers
├── frontend/           # React dashboard
│   └── src/
│       ├── components/ # UI components
│       ├── pages/      # Dashboard, Runs, Compare, Settings
│       └── utils/      # API client, formatters
├── docs/               # Requirements & design docs
│   ├── AWS_REQUIREMENTS.md
│   └── UI_UX_DESIGN.md
└── .github/workflows/  # CI/CD pipeline
```

## Quick Start

**New to AWS?** See the [Beginner Setup Guide](docs/BEGINNER_SETUP_GUIDE.md) for a step-by-step walkthrough.

### Prerequisites

- AWS CLI configured with credentials
- Terraform >= 1.5
- Node.js >= 20
- Python >= 3.12

### Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var="admin_email=your@email.com"
terraform apply -var="admin_email=your@email.com"
```

### Deploy Frontend

```bash
cd frontend
npm install
npm run dev   # Opens at http://localhost:3000
```

### Run Tests

```bash
# Manual trigger via AWS CLI
aws stepfunctions start-execution \
  --state-machine-arn $(terraform output -raw state_machine_arn) \
  --input '{"fault_type":"ec2-termination","target_resource":"auto"}'
```

## AWS Requirements

See [docs/AWS_REQUIREMENTS.md](docs/AWS_REQUIREMENTS.md) for the complete list of AWS services, IAM roles, permissions, DynamoDB schemas, and cost estimates.

## UI/UX Design

See [docs/UI_UX_DESIGN.md](docs/UI_UX_DESIGN.md) for the complete design specification including color system, typography, component library, and page layouts.

## Cost Estimate

Estimated monthly cost: **~$7.50–$15** (within AWS free tier for most services)

## License

MIT
# Cloud-project
