variable "environment" { type = string }
variable "aws_region" { type = string }
variable "account_id" { type = string }
variable "lambda_s3_bucket" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── Injection Lambda Role ─────────────────────────────────────────

resource "aws_iam_role" "injection_lambda" {
  name = "${local.name_prefix}-injection-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "injection_lambda" {
  name = "${local.name_prefix}-injection-lambda-policy"
  role = aws_iam_role.injection_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "fis:StartExperiment",
          "fis:StopExperiment",
          "fis:GetExperiment",
          "fis:ListExperiments",
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = var.aws_region
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── Monitor Lambda Role ───────────────────────────────────────────

resource "aws_iam_role" "monitor_lambda" {
  name = "${local.name_prefix}-monitor-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "monitor_lambda" {
  name = "${local.name_prefix}-monitor-lambda-policy"
  role = aws_iam_role.monitor_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics",
          "route53:GetHealthCheckStatus",
          "route53:ListHealthChecks",
          "ec2:DescribeInstanceStatus",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── Measurement Lambda Role ───────────────────────────────────────

resource "aws_iam_role" "measurement_lambda" {
  name = "${local.name_prefix}-measurement-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "measurement_lambda" {
  name = "${local.name_prefix}-measurement-lambda-policy"
  role = aws_iam_role.measurement_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── Scoring Lambda Role ───────────────────────────────────────────

resource "aws_iam_role" "scoring_lambda" {
  name = "${local.name_prefix}-scoring-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "scoring_lambda" {
  name = "${local.name_prefix}-scoring-lambda-policy"
  role = aws_iam_role.scoring_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "ssm:GetParameter",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── Audit Report Lambda Role ──────────────────────────────────────

resource "aws_iam_role" "audit_report_lambda" {
  name = "${local.name_prefix}-audit-report-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "audit_report_lambda" {
  name = "${local.name_prefix}-audit-report-lambda-policy"
  role = aws_iam_role.audit_report_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── External Audit Lambda Role ────────────────────────────────────

resource "aws_iam_role" "external_audit_lambda" {
  name = "${local.name_prefix}-external-audit-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "external_audit_lambda" {
  name = "${local.name_prefix}-external-audit-lambda-policy"
  role = aws_iam_role.external_audit_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── Alert Lambda Role ─────────────────────────────────────────────

resource "aws_iam_role" "alert_lambda" {
  name = "${local.name_prefix}-alert-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "alert_lambda" {
  name = "${local.name_prefix}-alert-lambda-policy"
  role = aws_iam_role.alert_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "dynamodb:GetItem",
          "ssm:GetParameter",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── API Lambda Role ───────────────────────────────────────────────

resource "aws_iam_role" "api_lambda" {
  name = "${local.name_prefix}-api-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "api_lambda" {
  name = "${local.name_prefix}-api-lambda-policy"
  role = aws_iam_role.api_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "s3:GetObject",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── Step Functions Execution Role ─────────────────────────────────

resource "aws_iam_role" "step_functions" {
  name = "${local.name_prefix}-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "step_functions" {
  name = "${local.name_prefix}-step-functions-policy"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "lambda:InvokeFunction"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── FIS Execution Role ────────────────────────────────────────────

resource "aws_iam_role" "fis_execution" {
  name = "${local.name_prefix}-fis-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "fis.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "fis_execution" {
  name = "${local.name_prefix}-fis-execution-policy"
  role = aws_iam_role.fis_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "ec2:TerminateInstances"
        Resource = "arn:aws:ec2:*:*:instance/*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/dr-test" = "true"
          }
        }
      }
    ]
  })
}

# ─── EventBridge Role ──────────────────────────────────────────────

resource "aws_iam_role" "eventbridge" {
  name = "${local.name_prefix}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge" {
  name = "${local.name_prefix}-eventbridge-policy"
  role = aws_iam_role.eventbridge.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "states:StartExecution"
      Resource = "*"
    }]
  })
}

# ─── Outputs ────────────────────────────────────────────────────────

output "injection_lambda_role_arn" {
  value = aws_iam_role.injection_lambda.arn
}

output "monitor_lambda_role_arn" {
  value = aws_iam_role.monitor_lambda.arn
}

output "measurement_lambda_role_arn" {
  value = aws_iam_role.measurement_lambda.arn
}

output "scoring_lambda_role_arn" {
  value = aws_iam_role.scoring_lambda.arn
}

output "audit_report_lambda_role_arn" {
  value = aws_iam_role.audit_report_lambda.arn
}

output "external_audit_lambda_role_arn" {
  value = aws_iam_role.external_audit_lambda.arn
}

output "alert_lambda_role_arn" {
  value = aws_iam_role.alert_lambda.arn
}

output "api_lambda_role_arn" {
  value = aws_iam_role.api_lambda.arn
}

# ─── SEO Report Lambda Role ───────────────────────────────────────

resource "aws_iam_role" "seo_report_lambda" {
  name = "${local.name_prefix}-seo-report-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "seo_report_lambda" {
  name = "${local.name_prefix}-seo-report-lambda-policy"
  role = aws_iam_role.seo_report_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

output "seo_report_lambda_role_arn" {
  value = aws_iam_role.seo_report_lambda.arn
}

# ─── Competitor Analysis Lambda Role ──────────────────────────────

resource "aws_iam_role" "competitor_analysis_lambda" {
  name = "${local.name_prefix}-competitor-analysis-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "competitor_analysis_lambda" {
  name = "${local.name_prefix}-competitor-analysis-lambda-policy"
  role = aws_iam_role.competitor_analysis_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

output "competitor_analysis_lambda_role_arn" {
  value = aws_iam_role.competitor_analysis_lambda.arn
}

# ─── PDF Report Lambda Role ───────────────────────────────────────

resource "aws_iam_role" "pdf_report_lambda" {
  name = "${local.name_prefix}-pdf-report-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "pdf_report_lambda" {
  name = "${local.name_prefix}-pdf-report-lambda-policy"
  role = aws_iam_role.pdf_report_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:HeadObject",
          "dynamodb:GetItem",
          "dynamodb:Query",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

output "pdf_report_lambda_role_arn" {
  value = aws_iam_role.pdf_report_lambda.arn
}

# ─── Client Intake Lambda Role ────────────────────────────────────

resource "aws_iam_role" "client_intake_lambda" {
  name = "${local.name_prefix}-client-intake-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "client_intake_lambda" {
  name = "${local.name_prefix}-client-intake-lambda-policy"
  role = aws_iam_role.client_intake_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      }
    ]
  })
}

output "client_intake_lambda_role_arn" {
  value = aws_iam_role.client_intake_lambda.arn
}

output "step_functions_role_arn" {
  value = aws_iam_role.step_functions.arn
}

output "fis_execution_role_arn" {
  value = aws_iam_role.fis_execution.arn
}

output "eventbridge_role_arn" {
  value = aws_iam_role.eventbridge.arn
}
