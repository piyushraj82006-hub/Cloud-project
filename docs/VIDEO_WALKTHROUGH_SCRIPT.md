# CloudGuard DR — Video Walkthrough Script

**Total Runtime: ~25 minutes**

---

## INTRO (0:00 – 1:30)

### Scene: Face cam / title card

**SCRIPT:**

> "Hey everyone! In this video, I'm going to walk you through setting up CloudGuard DR — an automated disaster recovery testing platform — completely from scratch. We'll go from an empty AWS account to a fully working system that actually breaks your servers on purpose, measures how fast they recover, and gives you a resilience score.
>
> By the end of this video, you'll have:
> - A React dashboard running on your computer
> - 8 Lambda functions deployed to AWS
> - A Step Functions pipeline that orchestrates disaster recovery tests
> - EC2 instances that get terminated and recover automatically
> - Email alerts when things go wrong
>
> Let's get started!"

### On-Screen: Show the final dashboard working

> "This is what we're building. A dark, minimal dashboard that shows your resilience score, recovery times, and lets you compare test runs side by side."

---

## PART 1: INSTALL PREREQUISITES (1:30 – 5:00)

### Scene: Screen recording with terminal

**SCRIPT:**

> "First, let's install the tools we need. I'm on a Mac, but I'll mention Windows commands too."

---

### 1A. Install Node.js (1:30 – 2:30)

**Terminal command:**
```bash
brew install node@20
```

> "We need Node.js version 20 for the React frontend. If you're on Windows, go to nodejs.org and download the LTS version."

**Verify:**
```bash
node --version
npm --version
```

> "You should see v20 and npm 10. That's good."

---

### 1B. Install Python (2:30 – 3:15)

**Terminal command:**
```bash
brew install python@3.12
```

> "Our Lambda functions run Python 3.12. On Windows, download from python.org and make sure to check 'Add Python to PATH' during installation."

**Verify:**
```bash
python3 --version
```

---

### 1C. Install AWS CLI (3:15 – 4:00)

**Terminal command:**
```bash
brew install awscli
```

> "The AWS CLI lets us talk to AWS from the terminal. On Windows, download the installer from aws.amazon.com/cli."

**Verify:**
```bash
aws --version
```

---

### 1D. Install Terraform (4:00 – 5:00)

**Terminal command:**
```bash
brew install terraform
```

> "Terraform is our infrastructure-as-code tool. It creates all the AWS resources for us automatically."

**Verify:**
```bash
terraform --version
```

> "Alright, all four tools are installed. Now let's set up AWS."

---

## PART 2: AWS ACCOUNT SETUP (5:00 – 10:00)

### Scene: Browser screen recording

---

### 2A. Create AWS Account (5:00 – 6:30)

> "Go to aws.amazon.com and click 'Create an AWS Account'."

**Show:** AWS signup page

> "Enter your email, create a password, and add your payment info. Don't worry — everything we're using today is within the free tier. You'll only pay about $7-15 a month for the EC2 instances, and that's it."

**Show:** Account creation steps

> "Choose the Basic Support plan — it's free."

---

### 2B. Create IAM User (6:30 – 8:00)

> "Now, NEVER use your root account for daily work. Let's create an IAM user."

**Show:** AWS Console → IAM

> "Search for IAM in the search bar, click Users, then Create User."

**Show each step:**
1. Username: `cloudguard-admin`
2. Check "Provide user access to the AWS Management Console"
3. Select "I want to create an IAM user"
4. Attach policy: `AdministratorAccess`
5. Click Create User

> "Save your sign-in URL and password somewhere safe."

---

### 2C. Create Access Keys (8:00 – 9:00)

> "Now we need access keys for the CLI."

**Show:** IAM → Users → cloudguard-admin → Security credentials

> "Click Create access key, select Command Line Interface, check the box, and create."

**Show:** Copy the keys

> "COPY THESE IMMEDIATELY. You can only see the secret key once. I'm saving mine in a text file."

---

### 2D. Configure AWS CLI (9:00 – 10:00)

**Terminal command:**
```bash
aws configure
```

> "Type aws configure and paste your keys when prompted."

**Show the prompts:**
```
AWS Access Key ID: AKIA...
AWS Secret Access Key: wJal...
Default region name: us-east-1
Default output format: json
```

> "Make sure you use us-east-1 — that's where FIS is available."

**Verify:**
```bash
aws sts get-caller-identity
```

> "If you see your account info, you're good to go!"

---

## PART 3: DEPLOY INFRASTRUCTURE (10:00 – 15:00)

### Scene: Terminal

---

### 3A. Navigate to Terraform (10:00 – 10:30)

**Terminal command:**
```bash
cd terraform
```

> "Let's go into the terraform folder."

---

### 3B. Initialize Terraform (10:30 – 11:30)

**Terminal command:**
```bash
terraform init
```

> "This downloads the AWS provider. It takes about 30 seconds."

**Show:** Terraform init output

> "See 'Terraform has been successfully initialized'? We're ready."

---

### 3C. Plan the Infrastructure (11:30 – 13:00)

**Terminal command:**
```bash
terraform plan -var="admin_email=your@email.com"
```

> "Replace your@email.com with your actual email. This plan shows us everything Terraform will create."

**Show:** Plan output scrolling

> "Look at this — 8 Lambda functions, 2 DynamoDB tables, 2 S3 buckets, a VPC with subnets, 2 EC2 instances, an API Gateway, Cognito user pool, Step Functions, SNS topic, CloudWatch alarms, and EventBridge schedule. That's about 50 AWS resources, all created automatically."

---

### 3D. Deploy Everything (13:00 – 15:00)

**Terminal command:**
```bash
terraform apply -var="admin_email=your@email.com"
```

> "Type 'yes' when prompted. This will take about 10-15 minutes."

**Show:** Apply progress

> "Terraform is creating all the resources now. I'll fast-forward through this..."

**[Fast forward 10 minutes]**

> "Done! See all the outputs? Save these — especially the api_url and state_machine_arn."

**Show:** Terraform outputs

---

## PART 4: CONFIGURE SERVICES (15:00 – 18:00)

### Scene: Browser + Terminal

---

### 4A. Confirm SNS Email (15:00 – 15:45)

> "Check your email. You should see an email from AWS Notifications."

**Show:** Email inbox

> "Click the Confirm subscription link. This ensures you'll get alerts when tests fail."

---

### 4B. Create Cognito User (15:45 – 17:00)

**Show:** AWS Console → Cognito

> "Go to Cognito in the AWS console. Find your user pool — it's called cloudguard-dev-users."

**Show each step:**
1. Click Users tab
2. Click Create user
3. Username: `admin`
4. Email: your email
5. Temporary password: `Temp1234!`
6. Click Create user

> "This is the user you'll use to log into the dashboard."

---

### 4C. Set Up Frontend (17:00 – 18:00)

**Terminal command:**
```bash
cd ../frontend
npm install
```

> "Install the frontend dependencies."

**Terminal command:**
```bash
echo "VITE_API_URL=$(cd ../terraform && terraform output -raw api_url)" > .env
```

> "This creates a .env file with your API URL."

**Terminal command:**
```bash
npm run dev
```

> "Start the development server."

**Show:** Terminal output showing localhost:3000

---

## PART 5: SEE IT WORK (18:00 – 22:00)

### Scene: Browser

---

### 5A. Open the Dashboard (18:00 – 19:00)

**Show:** Browser opening http://localhost:3000

> "Open localhost:3000 in your browser. You should see the CloudGuard DR dashboard with the dark theme."

**Show:** Dashboard with mock data

> "Right now it shows mock data because we haven't run a real test yet. But the UI is fully functional — you can navigate between pages, see the trend chart, and compare runs."

---

### 5B. Sign In (19:00 – 19:45)

> "If the dashboard asks you to sign in, use the Cognito user you created."

**Show:** Login flow

> "Enter your username and temporary password. You'll be asked to change it immediately."

---

### 5C. Trigger a Real Test (19:45 – 22:00)

**Terminal command:**
```bash
aws stepfunctions start-execution \
  --state-machine-arn $(cd terraform && terraform output -raw state_machine_arn) \
  --input '{"fault_type":"ec2-termination","target_resource":"auto"}'
```

> "Let's trigger a real disaster recovery test!"

**Show:** Command output

> "The test is now running. Here's what's happening step by step..."

**Show: AWS Console → Step Functions** (or describe verbally)

> "Step 1: The Injection Lambda finds an EC2 instance tagged with dr-test=true and terminates it using AWS FIS.
>
> Step 2: The Monitor Lambda watches CloudWatch and Route 53 until the system recovers.
>
> Step 3: The Measurement Lambda calculates RTO (Recovery Time Objective) — how long it took to recover.
>
> Step 4: The Scoring Lambda converts that into a resilience score from 0 to 100.
>
> Step 5: The Audit Report Lambda generates a JSON and HTML report and stores it in S3.
>
> Step 6: The Alert Lambda sends you an email if the score is below threshold."

**Show:** Email notification arriving

> "And here's the email alert! Our score was 82 out of 100, which is a pass."

---

## PART 6: EXPLAIN THE DASHBOARD (22:00 – 24:00)

### Scene: Browser screen recording

---

### 6A. Dashboard Overview (22:00 – 23:00)

**Show:** Dashboard page

> "Let me walk you through the dashboard."

**Point to each element:**
- "The big number at the top is your resilience score — 82 out of 100."
- "Below that, you see RTO and RPO with their targets and pass/fail indicators."
- "The trend chart shows how your score has changed over time."
- "Quick stats on the right give you a summary at a glance."
- "Recent runs table at the bottom lets you click into any test run."

---

### 6B. Other Pages (23:00 – 24:00)

**Show:** Runs page

> "The Runs page shows all test runs with filters for status and fault type. You can select two runs and compare them side by side."

**Show:** Compare page

> "The Compare page shows deltas between two runs — did the score improve or get worse?"

**Show:** Settings page

> "Settings lets you configure RTO/RPO targets, score thresholds, and alert email addresses."

---

## PART 7: WRAP UP (24:00 – 25:00)

### Scene: Face cam

**SCRIPT:**

> "And that's it! You now have a fully working disaster recovery testing platform.
>
> To recap what we built:
> - 8 Lambda functions that automate DR testing
> - A Step Functions pipeline that orchestrates everything
> - EC2 instances that get terminated and recover automatically
> - A React dashboard that shows your resilience score
> - Email alerts when tests fail
>
> The whole thing costs about $7-15 a month, and most of that is just the EC2 instances.
>
> When you're done testing, run 'terraform destroy' to remove everything and stop charges.
>
> If you found this helpful, drop a like and subscribe. See you in the next one!"

---

## B-ROLL / VISUAL NOTES

| Timestamp | Visual |
|-----------|--------|
| 0:00-1:30 | Title card → dashboard preview → face cam |
| 1:30-5:00 | Terminal screen recording |
| 5:00-10:00 | Browser screen recording (AWS console) |
| 10:00-15:00 | Terminal (terraform commands) |
| 15:00-18:00 | Browser + Terminal |
| 18:00-22:00 | Browser (dashboard + Step Functions) |
| 22:00-24:00 | Browser (dashboard pages) |
| 24:00-25:00 | Face cam |

---

## THUMBNAIL TEXT

```
BUILD A DR TESTING PLATFORM
From Zero to Working in 25 Minutes
AWS Lambda + Terraform + React
```

---

## VIDEO DESCRIPTION

```
CloudGuard DR — Automated Disaster Recovery Testing Platform

⏰ Timestamps:
0:00 - Intro
1:30 - Install Prerequisites (Node, Python, AWS CLI, Terraform)
5:00 - AWS Account & IAM Setup
10:00 - Deploy Infrastructure with Terraform
15:00 - Configure Cognito & Frontend
18:00 - See It Working (Dashboard + First Test)
22:00 - Dashboard Walkthrough
24:00 - Wrap Up

🔗 Links:
- GitHub: [your-repo-url]
- Beginner Guide: docs/BEGINNER_SETUP_GUIDE.md
- AWS Requirements: docs/AWS_REQUIREMENTS.md

💰 Estimated Cost: ~$7.50-$15/month (mostly EC2)
```
