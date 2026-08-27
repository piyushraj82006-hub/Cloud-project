# CloudGuard DR — Beginner Setup Guide

**This guide walks you through EVERYTHING from zero to a running app.**

---

## What You're Building

```
┌─────────────────────────────────────────────────────┐
│  React Dashboard (localhost:3000)                    │
│  ↓ talks to ↓                                        │
│  API Gateway → 8 Lambda Functions → DynamoDB + S3    │
│  ↓ triggered by ↓                                    │
│  Step Functions → AWS FIS (terminates EC2 instances)  │
│  ↓ monitors ↓                                        │
│  CloudWatch → RTO/RPO → Resilience Score → Alerts    │
└─────────────────────────────────────────────────────┘
```

**Estimated cost: ~$7.50–$15/month** (mostly from 2 tiny EC2 instances)

---

## PREREQUISITES (Install These First)

### Step 1: Install Node.js (for the frontend)

```bash
# macOS (with Homebrew)
brew install node@20

# Windows: download from https://nodejs.org (LTS version)

# Verify installation
node --version   # Should show v20.x.x
npm --version    # Should show 10.x.x
```

### Step 2: Install Python 3.12 (for Lambda functions)

```bash
# macOS
brew install python@3.12

# Windows: download from https://python.org
# ⚠️ CHECK "Add Python to PATH" during installation!

# Verify
python3 --version   # Should show Python 3.12.x
pip3 --version
```

### Step 3: Install AWS CLI

```bash
# macOS
brew install awscli

# Windows: download from https://aws.amazon.com/cli/

# Verify
aws --version
```

### Step 4: Install Terraform

```bash
# macOS
brew install terraform

# Windows: download from https://terraform.io/downloads

# Verify
terraform --version   # Should show v1.5.x or higher
```

---

## STEP-BY-STEP AWS SETUP

### Step 1: Create an AWS Account

1. Go to **https://aws.amazon.com**
2. Click **"Create an AWS Account"**
3. Enter your email, password, and payment info
4. Choose the **"Basic Support"** plan (free)
5. ⚠️ **You'll need a credit card** — but you'll stay within free tier

> **Tip:** If you're a student, sign up for **AWS Educate** or **AWS Academy** first — you get free credits!

### Step 2: Create an IAM User (Don't use root!)

1. Go to **AWS Console** → https://console.aws.amazon.com
2. Search for **"IAM"** in the search bar
3. Click **"Users"** → **"Create user"**
4. Enter username: `cloudguard-admin`
5. Check **"Provide user access to the AWS Management Console"**
6. Select **"I want to create an IAM user"**
7. Set permissions: **Attach policies directly** → search and check:
   - `AdministratorAccess` (for now — we'll tighten this later)
8. Click **"Create user"**
9. **SAVE THESE somewhere safe:**
   - Username: `cloudguard-admin`
   - Console sign-in URL
   - Password

### Step 3: Create Access Keys for CLI

1. While still in IAM → click on `cloudguard-admin`
2. Go to **"Security credentials"** tab
3. Click **"Create access key"**
4. Select **"Command Line Interface (CLI)"**
5. Check the confirmation box
6. Click **"Create access key"**
7. **COPY AND SAVE IMMEDIATELY:**
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJal...`

> ⚠️ You can only see the Secret Access Key ONCE!

### Step 4: Configure AWS CLI

Open your terminal and run:

```bash
aws configure
```

It will ask you for:
```
AWS Access Key ID [None]:        ← paste your Access Key ID
AWS Secret Access Key [None]:    ← paste your Secret Access Key
Default region name [None]:      ← type: us-east-1
Default output format [None]:    ← type: json
```

Verify it works:
```bash
aws sts get-caller-identity
```

You should see something like:
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/cloudguard-admin"
}
```

### Step 5: Install Terraform (if not done)

```bash
terraform --version
# If not installed: https://developer.hashicorp.com/terraform/install
```

---

## DEPLOY THE INFRASTRUCTURE

### Step 1: Initialize Terraform

```bash
cd terraform
terraform init
```

This downloads the AWS provider. You should see:
```
Terraform has been successfully initialized!
```

### Step 2: Review the Plan

```bash
terraform plan -var="admin_email=your-email@example.com"
```

This shows you everything Terraform will create:
- 8 Lambda functions
- 2 DynamoDB tables
- 2 S3 buckets
- VPC + subnets
- 2 EC2 instances (sample app)
- API Gateway
- Cognito user pool
- Step Functions state machine
- SNS topic
- CloudWatch alarms
- EventBridge schedule
- IAM roles (one per Lambda)

> ⚠️ This will take about 5-10 minutes to plan

### Step 3: Deploy Everything

```bash
terraform apply -var="admin_email=your-email@example.com"
```

Type `yes` when prompted.

> ⚠️ This takes 10-15 minutes. Go grab a coffee ☕

When done, you'll see outputs like:
```
Outputs:
api_url = "https://xxxxxxx.execute-api.us-east-1.amazonaws.com/prod"
dashboard_bucket = "cloudguard-dashboard-123456789012"
state_machine_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:cloudguard-dev-dr-test"
```

**SAVE THESE OUTPUTS!**

### Step 4: Confirm Your Email for SNS Alerts

1. Check your email inbox
2. You'll see an email from **"AWS Notifications"**
3. Click the **"Confirm subscription"** link
4. You should see "Subscription confirmed!"

### Step 5: Create a Cognito User

1. Go to **AWS Console** → search **"Cognito"**
2. Find the user pool: `cloudguard-dev-users`
3. Go to **"Users"** tab → **"Create user"**
4. Enter:
   - Username: `admin` (or any username)
   - Email: your email
   - Temporary password: `Temp1234!`
5. Click **"Create user"**
6. **Sign in to the dashboard** (see next step)
7. You'll be asked to change the password on first login

---

## SET UP THE FRONTEND

### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

### Step 2: Create Environment File

Create `frontend/.env` with your API URL:

```bash
echo "VITE_API_URL=$(terraform -chdir=../terraform output -raw api_url)" > .env
```

Or manually create `frontend/.env`:
```
VITE_API_URL=https://xxxxxxx.execute-api.us-east-1.amazonaws.com/prod
```

> Replace the URL with your actual `api_url` from the Terraform output

### Step 3: Run the Dashboard

```bash
npm run dev
```

Open **http://localhost:3000** in your browser.

You should see the CloudGuard DR dashboard with the dark theme.

### Step 4: Sign In

1. Enter your Cognito username and password
2. You'll be prompted to change your temporary password
3. After that, you're in!

---

## TESTING THE SYSTEM

### Option A: Trigger a Test Manually

```bash
aws stepfunctions start-execution \
  --state-machine-arn $(cd terraform && terraform output -raw state_machine_arn) \
  --input '{"fault_type":"ec2-termination","target_resource":"auto"}'
```

This will:
1. ✅ Terminate one of your EC2 instances (FIS)
2. ✅ Monitor until the other instance takes over
3. ✅ Measure recovery time (RTO) and data loss (RPO)
4. ✅ Calculate a resilience score (0-100)
5. ✅ Generate an audit report
6. ✅ Send you an email alert (if score is low)

### Option B: Wait for the Weekly Schedule

Tests run automatically every **Monday at 8 AM UTC** via EventBridge.

### Option C: Use the Dashboard npx skills add Leonxlnx/taste-skill

1. Go to **http://localhost:3000**
2. Click **"Run New Test"**
3. Select **"Full DR Test (Fault Injection)"**
4. Click **"Start DR Test"**

> ⚠️ This requires the API to be set up with the trigger endpoint

---

## WHAT EACH SERVICE DOES

| Service | What It Does | Cost |
|---------|-------------|------|
| **Lambda** | Runs your Python code (8 functions) | Free tier |
| **DynamoDB** | Stores test run results | Free tier |
| **S3** | Stores audit reports (JSON/HTML) | Free tier |
| **Step Functions** | Orchestrates the test pipeline | Free tier |
| **FIS** | Actually terminates EC2 instances | ~$0.10/min |
| **API Gateway** | Serves the REST API for the dashboard | Free tier |
| **Cognito** | Handles login/auth for the dashboard | Free tier |
| **SNS** | Sends email alerts when tests fail | Free tier |
| **EventBridge** | Runs tests on a schedule | Free tier |
| **EC2** | Sample app that gets "broken" during tests | ~$15/month for 2 |
| **VPC** | Network isolation (free) | Free |
| **CloudWatch** | Monitors Lambda logs and alarms | Free tier |

---

## TROUBLESHOOTING

### "aws configure" not found
→ Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

### "terraform: command not found"
→ Install Terraform: https://developer.hashicorp.com/terraform/install

### Terraform "Error: Error launching source instance"
→ You might have reached your EC2 instance limit
→ Go to AWS Console → Service Quotas → Amazon EC2 → check vCPU limits

### Terraform "Error: AccessDenied"
→ Your IAM user doesn't have enough permissions
→ Make sure you attached `AdministratorAccess` policy

### Frontend shows blank page
→ Make sure you ran `cd frontend && npm install` first
→ Check browser console (F12) for errors

### API returns 401 Unauthorized
→ Make sure you signed in with the Cognito user you created
→ Check the `.env` file has the correct API URL

---

## CLEANUP (When Done Testing)

To avoid charges, destroy everything:

```bash
cd terraform
terraform destroy -var="admin_email=your-email@example.com"
```

Type `yes` when prompted. This deletes ALL AWS resources created by this project.

---

## ESTIMATED MONTHLY COST

| Scenario | Cost |
|----------|------|
| **Free tier active** | ~$0 (just EC2 t3.micro) |
| **No free tier** | ~$7.50–$15/month |
| **With student credits** | $0 |

> The only real cost is the 2 EC2 instances (~$7.50 each/month without free tier)

---

## QUICK REFERENCE COMMANDS

```bash
# Frontend
cd frontend && npm run dev          # Start development server
cd frontend && npm run build        # Build for production
cd frontend && npm run typecheck    # Check for TypeScript errors
cd frontend && npm run lint         # Check for code issues

# Infrastructure
cd terraform && terraform init      # Initialize
cd terraform && terraform plan      # Preview changes
cd terraform && terraform apply     # Deploy
cd terraform && terraform destroy   # Remove everything

# AWS CLI
aws sts get-caller-identity                    # Check who you are
aws stepfunctions list-state-machines          # List your Step Functions
aws dynamodb scan --table-name cloudguard-dev-test-runs  # See test runs
```

---

## NEED HELP?

1. Check the [AWS Requirements](./AWS_REQUIREMENTS.md) for detailed specs
2. Check the [UI/UX Design](./UI_UX_DESIGN.md) for the frontend design
3. Look at the Lambda code in `lambdas/` — each has comments explaining what it does
