# CloudGuard DR — Full DR Test Setup Guide

**How to run fault injection tests on any site hosted on AWS**

---

## What Is a DR Test?

A DR (Disaster Recovery) test **intentionally breaks** part of your infrastructure, then measures how fast it recovers. CloudGuard DR automates this entire process:

```
You pick a site → We break it → We watch it recover → We score it → You get a report
```

The result is a **Resilience Score (0–100)** that tells you exactly how well your infrastructure handles failures.

---

## Understanding the Resilience Score

### What the Score Means

| Score Range | Grade | What It Means |
|-------------|-------|---------------|
| **90–100** | 🟢 Excellent | Your system recovered fast with minimal/no data loss. Production-ready DR. |
| **70–89** | 🟢 Passed | Recovery is within acceptable limits. Minor improvements possible. |
| **50–69** | 🟡 Warning | Recovery is slow or partial. Your SLAs may be at risk. |
| **30–49** | 🔴 Failed | Significant recovery delays. Immediate attention needed. |
| **0–29** | 🔴 Critical | System did not recover or took dangerously long. DR plan is broken. |

### How the Score Is Calculated

The score is a **weighted combination** of two metrics:

```
RTO Score = max(0, 100 - (actual_RTO / target_RTO × 50))    → 60% weight
RPO Score = max(0, 100 - (actual_RPO / target_RPO × 50))    → 40% weight

Final Score = (RTO Score × 0.6) + (RPO Score × 0.4)
```

#### What Are RTO and RPO?

| Metric | Full Name | What It Measures | Example |
|--------|-----------|------------------|---------|
| **RTO** | Recovery Time Objective | How long until the site is back online after failure | "It took 2m 34s to recover" |
| **RPO** | Recovery Point Objective | How much data was lost during the failure | "We lost 45 seconds of writes" |

#### Scoring Example

Suppose your targets are RTO = 5 minutes (300s) and RPO = 1 minute (60s):

| Scenario | Actual RTO | Actual RPO | RTO Score | RPO Score | Final Score | Status |
|----------|-----------|-----------|-----------|-----------|-------------|--------|
| Great recovery | 90s | 0s | 85 | 100 | **91** | ✅ Passed |
| Decent recovery | 152s | 45s | 75 | 63 | **70** | ✅ Passed |
| Slow recovery | 480s | 120s | 20 | 0 | **12** | ❌ Failed |
| No recovery | timeout | N/A | 0 | 0 | **0** | ❌ Failed |

#### Why RTO Is Weighted Higher (60%)

RTO (downtime) directly impacts users. If your site is down for 8 minutes, customers leave. RPO (data loss) matters too, but for most web applications the primary concern is "how fast are we back up?"

---

## Prerequisites

Before you can run a Full DR Test, you need:

### 1. AWS Account with CLI Access

```bash
# Verify your AWS CLI is configured
aws sts get-caller-identity

# You should see your account ID and IAM user
```

If not configured, see [BEGINNER_SETUP_GUIDE.md](./BEGINNER_SETUP_GUIDE.md).

### 2. Terraform Deployed

All infrastructure must be deployed:

```bash
cd terraform
terraform init
terraform apply -var="admin_email=your@email.com"
```

This creates:
- 8 Lambda functions (injection, monitor, measurement, scoring, audit-report, external-audit, alert, api)
- Step Functions state machine (orchestrates the pipeline)
- DynamoDB tables (stores results)
- S3 bucket (stores reports)
- FIS experiment template (fault injection)
- 2 EC2 sample app instances (system under test)
- VPC, ALB, Route 53, SNS, EventBridge, Cognito

### 3. Save Your Terraform Outputs

After `terraform apply`, save these:

```bash
terraform output

# You need:
# api_url              → for the frontend .env
# state_machine_arn    → for triggering tests
# sample_app_url       → the URL that gets "broken"
```

---

## Four Fault Types — When to Use Each

### 1. EC2 Termination (`ec2-termination`)

**What it does:** Uses AWS FIS to kill an EC2 instance tagged with `dr-test=true`.

**Tests:** Auto-scaling group recovery, AMI launch speed, ALB health check failover.

**Best for:** Any site running on EC2 behind an ALB.

**Requirements:**
- EC2 instances tagged `dr-test: true`
- An Auto Scaling Group (ASG) to launch replacements
- An ALB target group for health monitoring

```bash
# Tag your instances
aws ec2 create-tags \
  --resources i-0abc123def456 \
  --tags Key=dr-test,Value=true

# Run the test
aws stepfunctions start-execution \
  --state-machine-arn <STATE_MACHINE_ARN> \
  --input '{
    "fault_type": "ec2-termination",
    "target_resource": "auto",
    "target_url": "https://your-site.com"
  }'
```

**What "auto" does:** Finds any running instance tagged `dr-test=true` and terminates it.

---

### 2. DNS Failover (`dns-failover`)

**What it does:** Inverts a Route 53 health check, forcing DNS to failover to a secondary record.

**Tests:** Multi-region/multi-AZ DNS failover, Route 53 routing policies.

**Best for:** Sites using Route 53 failover routing (primary → secondary).

**Requirements:**
- Route 53 hosted zone with health checks
- Failover routing policy configured
- A secondary endpoint (another region, another AZ, or a static fallback page)

```bash
aws stepfunctions start-execution \
  --state-machine-arn <STATE_MACHINE_ARN> \
  --input '{
    "fault_type": "dns-failover",
    "target_url": "https://your-site.com"
  }'
```

**Auto-discovery:** The system matches your URL's domain against existing Route 53 health checks.

---

### 3. S3 Origin Block (`s3-origin-block`)

**What it does:** Adds a `Deny *` policy to an S3 bucket, blocking all GetObject requests.

**Tests:** CloudFront origin failover, static site redundancy, CDN fallback behavior.

**Best for:** Static websites or SPAs hosted on S3 behind CloudFront.

**Requirements:**
- S3 bucket hosting static content
- CloudFront distribution with origin failover configured (primary S3 → secondary S3 or custom origin)

```bash
aws stepfunctions start-execution \
  --state-machine-arn <STATE_MACHINE_ARN> \
  --input '{
    "fault_type": "s3-origin-block",
    "bucket_name": "my-static-site-bucket",
    "target_url": "https://my-site.cloudfront.net"
  }'
```

**Auto-discovery:** If you pass `target_url` with an S3 endpoint pattern (e.g., `my-bucket.s3.amazonaws.com`), the bucket name is extracted automatically.

---

### 4. Security Group (`security-group`)

**What it does:** Removes ingress ALLOW rules for a specific port (default: 443), blocking all traffic.

**Tests:** Network-level recovery, security group automation, port-level failover.

**Best for:** Testing if your monitoring detects blocked traffic and if automation can restore access.

**Requirements:**
- Security group ID (or auto-discover from VPC)
- Port number to block (default: 443)

```bash
aws stepfunctions start-execution \
  --state-machine-arn <STATE_MACHINE_ARN> \
  --input '{
    "fault_type": "security-group",
    "security_group_id": "sg-0abc123def456",
    "port": 443,
    "target_url": "https://your-site.com"
  }'
```

**Auto-discovery:** If no `security_group_id` is provided, it finds the default SG in the default VPC.

---

## Running a DR Test — Step by Step

### Option A: Via the Dashboard (Recommended)

1. Open the frontend at `http://localhost:3000`
2. Navigate to **New Audit**
3. Select **"Full DR Test (Fault Injection)"**
4. Enter the **Target Site URL** (the URL the monitor will poll to confirm recovery)
5. Choose a **Fault Type** (EC2 Termination, DNS Failover, S3 Origin Block, or Security Group)
6. Fill in any fault-specific fields (port, bucket name, security group ID)
7. Click **"Start DR Test"**
8. The test runs through the pipeline automatically
9. View results on the **Dashboard** or **Runs** page

### Option B: Via AWS CLI

```bash
# Get your state machine ARN
STATE_MACHINE_ARN=$(cd terraform && terraform output -raw state_machine_arn)

# Run EC2 termination test
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{
    "fault_type": "ec2-termination",
    "target_resource": "auto",
    "target_url": "https://your-site.com"
  }'
```

### Option C: Automatic Weekly Schedule

Tests run automatically every **Monday at 8:00 AM UTC** via EventBridge. You can change the schedule in `terraform/modules/eventbridge/`.

---

## What Happens During a Test (The Pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: INJECT                                              │
│  Lambda breaks the target (EC2 kill / DNS flip / S3 block)  │
│  Timestamp recorded: injection_timestamp                     │
│  Duration: ~5–15 seconds                                     │
├─────────────────────────────────────────────────────────────┤
│  Step 2: MONITOR                                             │
│  Lambda polls every 15s for up to 10 minutes:                │
│    • HTTP health check on target_url                         │
│    • ALB target group health                                 │
│    • EC2 instance status (for replacements)                  │
│    • Route 53 health check status                            │
│  Timestamp recorded: recovery_timestamp                      │
├─────────────────────────────────────────────────────────────┤
│  Step 3: MEASURE                                             │
│  Lambda calculates:                                          │
│    • RTO = recovery_timestamp - injection_timestamp          │
│    • RPO = data loss window (0 for stateless apps)           │
├─────────────────────────────────────────────────────────────┤
│  Step 4: SCORE                                               │
│  Lambda converts RTO/RPO into a 0–100 resilience score      │
│  Stores the result in DynamoDB (TestRuns table)              │
│  Determines Pass/Fail against configured threshold           │
├─────────────────────────────────────────────────────────────┤
│  Step 5: REPORT                                              │
│  Lambda generates JSON + HTML audit report                   │
│  Uploads to S3 (reports bucket)                              │
│  Stores pointer in DynamoDB (AuditReports table)             │
├─────────────────────────────────────────────────────────────┤
│  Step 6: ALERT                                               │
│  Lambda checks if score is below threshold                   │
│  If failed → sends SNS email alert with details              │
│  Alert includes: score, RTO/RPO, failure reasons             │
└─────────────────────────────────────────────────────────────┘
```

### Automatic Fault Restoration

After monitoring completes, the system **automatically restores** the fault:

| Fault Type | What Gets Restored |
|---|---|
| `ec2-termination` | Nothing — ASG launches a new instance automatically |
| `dns-failover` | Route 53 health check is un-inverted (back to normal) |
| `s3-origin-block` | S3 bucket policy is restored to its original state |
| `security-group` | Ingress rules are re-added to the security group |

---

## Running on Any Site (Setup Checklist)

### For Sites Already in Your AWS Account

| Step | Action | Command/Where |
|------|--------|---------------|
| 1 | Tag EC2 instances | `aws ec2 create-tags --resources <instance-id> --tags Key=dr-test,Value=true` |
| 2 | Ensure ALB health checks work | AWS Console → EC2 → Target Groups → Health checks |
| 3 | Verify Route 53 (if using DNS failover) | AWS Console → Route 53 → Health checks |
| 4 | Deploy CloudGuard DR infra | `cd terraform && terraform apply` |
| 5 | Set target URL in the test input | The URL the monitor will poll |
| 6 | Run the test | Dashboard or CLI |

### For Client Sites in a Different AWS Account

This requires **cross-account IAM access** (not yet built — see Roadmap below):

1. **Client creates an IAM role** with a trust policy allowing your account:
   ```json
   {
     "Effect": "Allow",
     "Principal": { "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:root" },
     "Action": "sts:AssumeRole"
   }
   ```

2. **Client attaches permissions** to that role:
   - `ec2:TerminateInstances` (for EC2 tests)
   - `ec2:DescribeInstances`
   - `route53:*` (for DNS failover tests)
   - `s3:PutBucketPolicy`, `s3:GetBucketPolicy` (for S3 tests)
   - `ec2:AuthorizeSecurityGroupIngress`, `ec2:RevokeSecurityGroupIngress` (for SG tests)

3. **You pass the role ARN** when triggering the test:
   ```bash
   aws stepfunctions start-execution \
     --input '{
       "fault_type": "ec2-termination",
       "target_url": "https://client-site.com",
       "assume_role_arn": "arn:aws:iam::CLIENT_ACCOUNT:role/CloudGuardDR-Access"
     }'
   ```

### For Non-AWS Sites

Full fault injection is **not possible** on sites hosted outside AWS (you can't kill their servers). Instead, use:

- **External Site Audit** — Health check, SSL, DNS, response time
- **SEO Audit** — Full SEO analysis with AI insights
- **Competitor Analysis** — Compare against competitor sites

---

## Configuring Thresholds

Thresholds determine what counts as "Passed" vs "Failed":

### Via Terraform Variables

```bash
terraform apply \
  -var="admin_email=your@email.com" \
  -var="rto_target_seconds=300" \
  -var="rpo_target_seconds=60" \
  -var="score_threshold=70"
```

### Via the Dashboard Settings Page

1. Go to **Settings**
2. Update **RTO Target**, **RPO Target**, and **Score Threshold**
3. Click **Save Changes**

### Via SSM Parameter Store (Directly)

```bash
# Update RTO target to 5 minutes
aws ssm put-parameter \
  --name "/cloudguard-dev/rto-target-seconds" \
  --value "300" --type String --overwrite

# Update RPO target to 1 minute
aws ssm put-parameter \
  --name "/cloudguard-dev/rpo-target-seconds" \
  --value "60" --type String --overwrite

# Update score threshold to 70
aws ssm put-parameter \
  --name "/cloudguard-dev/score-threshold" \
  --value "70" --type String --overwrite
```

---

## Reading the Report

After each test, a report is generated with:

### Resilience Metrics Section
- **Score**: 0–100 with color coding (green ≥ 70, yellow 50–69, red < 50)
- **Status**: PASSED or FAILED
- **RTO**: Actual recovery time vs target (e.g., "152s / 300s ✓")
- **RPO**: Actual data loss vs target (e.g., "0s / 60s ✓")

### Score Interpretation Guide (in the report)
- **90–100**: Infrastructure is battle-tested. DR plan is working excellently.
- **70–89**: Recovery meets SLA. Consider optimizing for even faster recovery.
- **50–69**: Recovery is borderline. Review auto-scaling policies and health check intervals.
- **30–49**: Significant issues. RTO/RPO targets are being missed. Take action.
- **0–29**: DR plan is effectively broken. Immediate remediation required.

### Site Health Checks Section
- **HTTPS Valid**: Is the SSL certificate working?
- **DNS Failover**: Does DNS resolve correctly?
- **Response Time**: How fast does the site respond (in ms)?
- **HTTP Status**: What status code does the site return?

---

## Alerts

When a test fails, CloudGuard DR sends an **SNS email alert** with:

```
CloudGuard DR Test Run Alert
==================================================

Run ID:       run-d4e5f6
Status:       Failed
Score:        45/100
Timestamp:    2026-08-22 08:10:00 UTC

Alert Reasons:
  • Score 45 is below threshold 70
  • RTO exceeded target: 8m 12s > 5m 0s
  • RPO exceeded target: 2m 30s > 1m 0s

Metrics:
  RTO: 8m 12s (target: 5m 0s)
  RPO: 2m 30s (target: 1m 0s)
==================================================
```

---

## Troubleshooting

### Test Stuck at "Monitor" Stage
- **Cause**: The system can't detect recovery (target_url not responding, no healthy instances).
- **Fix**: Check that your ASG is configured to launch replacement instances. Verify the `target_url` is accessible. Monitor times out after 10 minutes.

### Score Is 0
- **Cause**: The system couldn't measure recovery (measurement failed).
- **Fix**: Check CloudWatch logs for the Monitor Lambda. Ensure the target_url responds with HTTP 2xx/3xx after recovery.

### No FIS Template Found
- **Cause**: The FIS experiment template wasn't created by Terraform.
- **Fix**: Run `terraform apply` again. Verify in AWS Console → FIS → Experiment Templates.

### No Instances Found with `dr-test=true` Tag
- **Cause**: No running EC2 instances have the required tag.
- **Fix**: `aws ec2 create-tags --resources <instance-id> --tags Key=dr-test,Value=true`

### Alert Email Not Received
- **Cause**: SNS subscription not confirmed.
- **Fix**: Check your email for the SNS confirmation link and click it.

---

## Quick Reference

```bash
# Run EC2 termination test
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"fault_type":"ec2-termination","target_resource":"auto","target_url":"https://your-site.com"}'

# Run DNS failover test
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"fault_type":"dns-failover","target_url":"https://your-site.com"}'

# Run S3 origin block test
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"fault_type":"s3-origin-block","bucket_name":"my-bucket","target_url":"https://cdn.your-site.com"}'

# Run security group test
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"fault_type":"security-group","port":443,"target_url":"https://your-site.com"}'

# Check test results
aws dynamodb scan --table-name cloudguard-dev-test-runs

# View a specific run
aws dynamodb get-item --table-name cloudguard-dev-test-runs --key '{"run_id":{"S":"run-abc123"}}'
```
