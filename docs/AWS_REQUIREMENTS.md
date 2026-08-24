# CloudGuard DR — AWS Requirements Document

**Version:** 1.0 (MVP)
**Date:** August 22, 2026
**Project:** CloudGuard DR — Automated Disaster Recovery Testing Platform

---

## 1. AWS Services Required

### 1.1 Core Compute

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **AWS Lambda** | Backend logic (8 functions) | Python 3.12 runtime, max 15 min timeout, 128MB–512MB memory |
| **AWS Step Functions** | Test orchestration state machine | Standard workflow, 25,000 executions free tier |
| **Amazon EC2** | Sample 3-tier app (system under test) | t3.micro or t3.small, 2 instances across AZs |

### 1.2 Fault Injection & Resilience

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **AWS Fault Injection Simulator (FIS)** | Automated fault injection (EC2 termination) | Experiment templates scoped by `dr-test:true` tag |
| **Amazon Route 53** | DNS failover routing & health checks | Health checks on sample app ALB, failover routing policy |
| **Amazon CloudWatch** | Metrics source for RTO/RPO calculation | Custom metrics + standard EC2/ALB metrics |

### 1.3 Data & Storage

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Amazon DynamoDB** | Test run records, audit report pointers | On-demand capacity, 2 tables |
| **Amazon S3** | Report storage (JSON/HTML), dashboard hosting | 2 buckets: reports (private), dashboard (public-read) |

### 1.4 Networking & Security

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Amazon VPC** | Network isolation for sample app & Lambda | 2 public subnets, 2 private subnets, Internet Gateway |
| **AWS IAM** | Least-privilege roles for all services | Per-function Lambda roles, FIS execution role, Step Functions role |
| **AWS Cognito** | Dashboard authentication | User pool with 1 Admin user (MVP) |
| **AWS Secrets Manager** | Store API keys, DB credentials | No plaintext secrets in Lambda env vars |
| **AWS SSM Parameter Store** | Store non-sensitive config (thresholds, ARNs) | Parameter store for RTO/RPO target values |

### 1.5 API & Frontend

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Amazon API Gateway** | REST API for dashboard | Cognito-authorizer, regional endpoint |
| **AWS Certificate Manager (ACM)** | HTTPS for custom domain (optional) | Free SSL cert if using custom domain |

### 1.6 Alerting & Monitoring

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Amazon SNS** | Alert notifications on missed targets | Email subscription for MVP |
| **Amazon EventBridge** | Scheduled test triggers | Cron schedule (weekly by default) |
| **Amazon CloudWatch Alarms** | Step Functions failure monitoring | Alarm on execution failures → SNS |

### 1.7 CI/CD

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **GitHub Actions** | CI/CD pipeline | terraform plan on PR, terraform apply on merge |
| **Amazon ECR** | Container registry (if using containerized Lambdas) | Optional — zip deployment preferred for MVP |

---

## 2. IAM Roles & Policies (Detailed)

### 2.1 Lambda Execution Roles (one per function)

#### Injection Lambda Role
```json
{
  "Effect": "Allow",
  "Action": [
    "fis:StartExperiment",
    "fis:StopExperiment",
    "fis:GetExperiment",
    "fis:ListExperiments",
    "ec2:DescribeInstances",
    "ec2:DescribeInstanceStatus",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "aws:RequestedRegion": "us-east-1"
    }
  }
}
```

#### Monitor Lambda Role
```json
{
  "Effect": "Allow",
  "Action": [
    "cloudwatch:GetMetricStatistics",
    "cloudwatch:ListMetrics",
    "route53:GetHealthCheckStatus",
    "route53:ListHealthChecks",
    "ec2:DescribeInstanceStatus",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

#### Measurement Lambda Role
```json
{
  "Effect": "Allow",
  "Action": [
    "cloudwatch:GetMetricStatistics",
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

#### Scoring Lambda Role
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "dynamodb:GetItem",
    "dynamodb:Query",
    "ssm:GetParameter",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

#### Audit Report Lambda Role
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:GetObject",
    "dynamodb:PutItem",
    "dynamodb:GetItem",
    "dynamodb:Query",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

#### External Audit Lambda Role
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "dynamodb:PutItem",
    "dynamodb:GetItem",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

#### Alert Lambda Role
```json
{
  "Effect": "Allow",
  "Action": [
    "sns:Publish",
    "dynamodb:GetItem",
    "ssm:GetParameter",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

#### API Lambda Role (read-only)
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:Query",
    "dynamodb:Scan",
    "s3:GetObject",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

### 2.2 Step Functions Execution Role
```json
{
  "Effect": "Allow",
  "Action": [
    "lambda:InvokeFunction",
    "logs:CreateLogDelivery",
    "logs:GetLogDelivery",
    "logs:UpdateLogDelivery",
    "logs:DeleteLogDelivery",
    "logs:ListLogDeliveries",
    "logs:PutResourcePolicy",
    "logs:DescribeResourcePolicies",
    "logs:DescribeLogGroups",
    "xray:PutTraceSegments",
    "xray:PutTelemetryRecords",
    "xray:GetSamplingRules",
    "xray:GetSamplingTargets",
    "xray:GetSamplingStatisticSummaries"
  ],
  "Resource": "*"
}
```

### 2.3 FIS Execution Role
```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:TerminateInstances"
  ],
  "Resource": "arn:aws:ec2:*:*:instance/*",
  "Condition": {
    "StringEquals": {
      "aws:ResourceTag/dr-test": "true"
    }
  }
}
```

### 2.4 EventBridge Role
```json
{
  "Effect": "Allow",
  "Action": [
    "states:StartExecution"
  ],
  "Resource": "arn:aws:states:*:*:stateMachine:CloudGuardDR-*"
}
```

---

## 3. DynamoDB Table Definitions

### 3.1 TestRuns Table

| Property | Value |
|----------|-------|
| **Table Name** | `CloudGuardDR-TestRuns` |
| **Partition Key** | `run_id` (String) |
| **Billing Mode** | PAY_PER_REQUEST (on-demand) |
| **TTL Attribute** | `ttl` (optional, for old run cleanup) |

**Attributes:**
```
run_id: String (PK)
timestamp: String (ISO 8601)
fault_type: String (e.g., "ec2-termination")
target_resource: String (EC2 instance ID)
rto_seconds: Number
rpo_seconds: Number
resilience_score: Number (0-100)
status: String ("Passed" | "Failed" | "Incomplete")
report_s3_key: String
rto_target: Number
rpo_target: Number
stage_timestamps: Map (Inject, Monitor, Measure, Score, Report timestamps)
```

### 3.2 AuditReports Table

| Property | Value |
|----------|-------|
| **Table Name** | `CloudGuardDR-AuditReports` |
| **Partition Key** | `report_id` (String) |
| **GSI** | `run_id-index` (GSI on `run_id`) |
| **Billing Mode** | PAY_PER_REQUEST (on-demand) |

**Attributes:**
```
report_id: String (PK)
run_id: String (nullable — null for external site audits)
target_url: String
https_valid: Boolean
dns_failover_ok: Boolean
response_time_ms: Number (nullable)
http_status_code: Number
ssl_expiry_days: Number
generated_at: String (ISO 8601)
fault_type: String (nullable for external)
rto_seconds: Number (nullable for external)
rpo_seconds: Number (nullable for external)
resilience_score: Number (nullable for external)
s3_report_key: String
```

---

## 4. S3 Bucket Configuration

### 4.1 Reports Bucket (`cloudguard-reports-{account_id}`)

```hcl
bucket = "cloudguard-reports-${data.aws_caller_identity.current.account_id}"

# Public access: BLOCKED
block_public_acls       = true
block_public_policy     = true
ignore_public_acls      = true
restrict_public_buckets = true

# Versioning: Enabled
# Encryption: AES-256 (SSE-S3)
# Lifecycle: Delete objects older than 90 days (optional)

# Bucket policy: Lambda can write, API can read via signed URLs
```

**Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowLambdaWrite",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/cloudguard-audit-report-lambda"
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::cloudguard-reports-*/*"
    },
    {
      "Sid": "AllowLambdaRead",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/cloudguard-api-lambda"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::cloudguard-reports-*/*"
    }
  ]
}
```

### 4.2 Dashboard Bucket (`cloudguard-dashboard-{account_id}`)

```hcl
bucket = "cloudguard-dashboard-${data.aws_caller_identity.current.account_id}"

# Public access: ALLOW for GetObject only
# Website hosting: Enabled
# Index document: index.html
# Error document: error.html
# Encryption: AES-256
```

**Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForStaticAssets",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::cloudguard-dashboard-*/*"
    }
  ]
}
```

---

## 5. API Gateway Configuration

### 5.1 REST API

| Property | Value |
|----------|-------|
| **Name** | `CloudGuardDR-API` |
| **Type** | REST API (regional) |
| **Auth** | Cognito User Pool Authorizer |
| **Stage** | `prod` |

### 5.2 Endpoints

| Method | Path | Lambda | Auth |
|--------|------|--------|------|
| GET | `/runs` | api-list-runs | Cognito JWT |
| GET | `/runs/{run_id}` | api-get-run | Cognito JWT |
| GET | `/runs/{run_id}/report` | api-get-report | Cognito JWT |
| POST | `/compare` | api-compare | Cognito JWT |
| POST | `/audit/external` | external-audit | Cognito JWT |
| POST | `/test/trigger` | api-trigger-test | Cognito JWT (Admin) |
| GET | `/health` | (none) | None |

### 5.3 CORS Configuration

```yaml
Access-Control-Allow-Origin: "*"
Access-Control-Allow-Headers: "Content-Type,Authorization"
Access-Control-Allow-Methods: "GET,POST,OPTIONS"
```

---

## 6. Cognito Configuration

### 6.1 User Pool

| Property | Value |
|----------|-------|
| **Pool Name** | `CloudGuardDR-Users` |
| **Sign-in** | Email |
| **MFA** | Optional (OFF for MVP) |
| **Password Policy** | Min 8 chars, requires uppercase + lowercase + number |
| **Token Expiry** | Access: 1 hour, Refresh: 30 days |

### 6.2 App Client

| Property | Value |
|----------|-------|
| **Client Name** | `CloudGuardDR-Dashboard` |
| **Auth Flows** | ALLOW_USER_SRP_AUTH, ALLOW_REFRESH_TOKEN_AUTH |
| **Token Validity** | Access: 1 hour, Refresh: 30 days |

### 6.3 Domain

| Property | Value |
|----------|-------|
| **Domain Prefix** | `cloudguarddr-{unique-suffix}` |

---

## 7. Route 53 Configuration

### 7.1 Health Check

| Property | Value |
|----------|-------|
| **Type** | HTTP/HTTPS |
| **Port** | 80 (or 443 for HTTPS) |
| **Path** | `/health` |
| **Interval** | 30 seconds |
| **Failure Threshold** | 3 |
| **Request Interval** | Fast (10 seconds) |

### 7.2 Failover Routing

| Record | Primary | Secondary |
|--------|---------|-----------|
| `sample-app.example.com` | ALB in AZ-1 (us-east-1a) | ALB in AZ-2 (us-east-1b) |

**Routing Policy:** Failover (primary/secondary)
**Health Check:** Associated with primary record

---

## 8. EventBridge Schedule

### 8.1 Weekly Test Schedule

| Property | Value |
|----------|-------|
| **Name** | `CloudGuardDR-WeeklyTest` |
| **Schedule** | `cron(0 8 ? * MON *)` (Every Monday at 8 AM UTC) |
| **Target** | Step Functions state machine |
| **Input** | `{"fault_type": "ec2-termination", "target_resource": "auto"}` |

---

## 9. SNS Configuration

### 9.1 Alert Topic

| Property | Value |
|----------|-------|
| **Topic Name** | `CloudGuardDR-Alerts` |
| **Display Name** | `CloudGuardDR` |
| **Protocol** | Email (MVP), HTTP/HTTPS (post-MVP) |
| **Subscription** | Admin email address |

---

## 10. Secrets Manager & SSM

### 10.1 Secrets Manager

| Secret | Content |
|--------|---------|
| `cloudguard/dr-test-credentials` | Database credentials (if RDS used), API keys |

### 10.2 SSM Parameters

| Parameter | Value | Type |
|-----------|-------|------|
| `/cloudguard/rto-target-seconds` | `300` (5 min) | String |
| `/cloudguard/rpo-target-seconds` | `60` (1 min) | String |
| `/cloudguard/score-threshold` | `70` | String |
| `/cloudguard/sns-topic-arn` | `arn:aws:sns:us-east-1:ACCOUNT:CloudGuardDR-Alerts` | String |
| `/cloudguard/dynamodb-test-runs-table` | `CloudGuardDR-TestRuns` | String |
| `/cloudguard/dynamodb-audit-reports-table` | `CloudGuardDR-AuditReports` | String |
| `/cloudguard/s3-reports-bucket` | `cloudguard-reports-ACCOUNT` | String |

---

## 11. CloudWatch Configuration

### 11.1 Log Groups (one per Lambda)

| Log Group | Retention |
|-----------|-----------|
| `/aws/lambda/cloudguard-injection` | 14 days |
| `/aws/lambda/cloudguard-monitor` | 14 days |
| `/aws/lambda/cloudguard-measurement` | 14 days |
| `/aws/lambda/cloudguard-scoring` | 14 days |
| `/aws/lambda/cloudguard-audit-report` | 14 days |
| `/aws/lambda/cloudguard-external-audit` | 14 days |
| `/aws/lambda/cloudguard-alert` | 14 days |
| `/aws/lambda/cloudguard-api` | 14 days |

### 11.2 CloudWatch Alarms

| Alarm | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| `CloudGuardDR-StepFunctionsFailure` | `ExecutionsFailed` (Step Functions) | >= 1 | Publish to SNS topic |
| `CloudGuardDR-HighRTO` | Custom metric `rto_seconds` | > 300 | Publish to SNS topic |

---

## 12. EC2 / Sample App (System Under Test)

### 12.1 Instance Configuration

| Property | Value |
|----------|-------|
| **AMI** | Amazon Linux 2023 |
| **Instance Type** | t3.micro (free tier eligible) |
| **Count** | 2 (one per AZ) |
| **Tag** | `dr-test: true` (required for FIS targeting) |
| **Tag** | `Name: CloudGuardDR-SampleApp-{az}` |
| **User Data** | Installs nginx, creates `/health` endpoint returning 200 OK |
| **Security Group** | Inbound: 80 (HTTP) from anywhere, 443 (HTTPS) from anywhere |
| **IAM Role** | SSM managed instance role (for Systems Manager access) |

### 12.2 Application Load Balancer

| Property | Value |
|----------|-------|
| **Name** | `CloudGuardDR-SampleApp-ALB` |
| **Scheme** | Internet-facing |
| **Listener** | HTTP:80 → Target Group |
| **Target Group** | Both EC2 instances, health check on `/health` |
| **Health Check Path** | `/health` |
| **Healthy Threshold** | 2 |
| **Unhealthy Threshold** | 3 |
| **Interval** | 10 seconds |

---

## 13. VPC Configuration

```
VPC: cloudguard-vpc
├── CIDR: 10.0.0.0/16
├── Public Subnets
│   ├── 10.0.1.0/24 (us-east-1a) — ALB, EC2
│   └── 10.0.2.0/24 (us-east-1b) — ALB, EC2
├── Private Subnets
│   ├── 10.0.3.0/24 (us-east-1a) — Lambda (optional)
│   └── 10.0.4.0/24 (us-east-1b) — Lambda (optional)
├── Internet Gateway
├── Route Tables
│   ├── Public RT → IGW
│   └── Private RT → NAT Gateway (optional)
└── Security Groups
    ├── cloudguard-alb-sg — Inbound 80/443 from 0.0.0.0/0
    ├── cloudguard-ec2-sg — Inbound 80 from ALB SG only
    └── cloudguard-lambda-sg — Outbound all (for AWS API calls)
```

---

## 14. Cost Estimate (MVP — Free Tier / Student Credits)

| Service | Free Tier Allowance | Estimated Monthly Cost |
|---------|--------------------|-----------------------|
| **Lambda** | 1M requests/month, 400K GB-sec | $0 (within free tier) |
| **DynamoDB** | 25 GB storage, 25 WCU, 25 RCU | $0 (on-demand within free tier) |
| **S3** | 5 GB storage, 20K GET, 2K PUT | $0 (within free tier) |
| **Step Functions** | 4,000 state transitions/month | $0 (within free tier) |
| **FIS** | $0.10/min per experiment | ~$0.40/month (weekly 4-min tests) |
| **API Gateway** | 1M REST API calls | $0 (within free tier) |
| **Cognito** | 50K MAUs | $0 (within free tier) |
| **SNS** | 1M publishes, 100K deliveries | $0 (within free tier) |
| **Route 53** | Health checks: 50 free | $0 (within free tier) |
| **CloudWatch** | 10 custom metrics, 5GB log ingestion | $0 (within free tier) |
| **EC2 (sample app)** | t3.micro: 750 hrs/month | $0 (within free tier for 1 instance; 2 instances = ~$7.50) |
| **VPC** | No charge for VPC/subnets | $0 |
| **Secrets Manager** | 10,000 free API calls | $0 (within free tier) |
| **Total Estimated** | | **~$7.50–$15/month** |

**Notes:**
- EC2 is the only significant cost — 2× t3.micro = ~$15/month if no free tier
- FIS experiments are cheap (~$0.10/min)
- All other services are well within free tier limits for weekly testing
- Student credits / AWS Educate can cover the full cost

---

## 15. AWS Region

| Property | Value |
|----------|-------|
| **Primary Region** | `us-east-1` (N. Virginia) |
| **Reason** | Most services available first, cheapest pricing, FIS availability |

---

## 16. Tags & Naming Convention

| Tag | Value |
|-----|-------|
| `Project` | `CloudGuardDR` |
| `Environment` | `dev` or `demo` |
| `ManagedBy` | `Terraform` |
| `dr-test` | `true` (on FIS-target resources only) |

**Naming Pattern:** `cloudguard-{resource-type}-{purpose}`
Examples:
- `cloudguard-lambda-injection`
- `cloudguard-dynamodb-test-runs`
- `cloudguard-s3-reports`
- `cloudguard-fis-instance-termination`

---

## 17. Security Checklist (MVP)

- [ ] All S3 buckets block public access (except dashboard bucket for GetObject only)
- [ ] No Lambda function has wildcard IAM permissions
- [ ] FIS experiments scoped by resource tag only
- [ ] Cognito JWT required for all API endpoints except `/health`
- [ ] Secrets stored in Secrets Manager, not Lambda env vars
- [ ] VPC flow logs enabled (optional but recommended)
- [ ] CloudTrail enabled for API audit logging
- [ ] DynamoDB encryption at rest enabled (default AWS managed key)
- [ ] S3 server-side encryption enabled (AES-256)
- [ ] Lambda functions use least-privilege IAM roles
