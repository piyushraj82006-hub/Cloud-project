variable "environment" { type = string }
variable "aws_region" { type = string }
variable "account_id" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }

variable "injection_role_arn" { type = string }
variable "monitor_role_arn" { type = string }
variable "measurement_role_arn" { type = string }
variable "scoring_role_arn" { type = string }
variable "audit_report_role_arn" { type = string }
variable "external_audit_role_arn" { type = string }
variable "alert_role_arn" { type = string }
variable "api_role_arn" { type = string }
variable "seo_report_role_arn" { type = string }
variable "competitor_analysis_role_arn" { type = string }
variable "pdf_report_role_arn" { type = string }
variable "pdf_report_layer_arn" {
  type    = string
  default = ""
}
variable "client_intake_role_arn" { type = string }

variable "test_runs_table_name" { type = string }
variable "audit_reports_table_name" { type = string }
variable "clients_table_name" { type = string }
variable "reports_bucket_id" { type = string }
variable "sns_topic_arn" { type = string }
variable "rto_target_ssm_arn" { type = string }
variable "rpo_target_ssm_arn" { type = string }
variable "score_threshold_ssm_arn" { type = string }
variable "sns_topic_ssm_arn" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── Lambda Deployment Package ─────────────────────────────────────

data "archive_file" "lambda" {
  for_each = toset([
    "injection",
    "monitor",
    "measurement",
    "scoring",
    "audit-report",
    "external-audit",
    "alert",
    "api",
    "seo-report",
    "competitor-analysis",
    "pdf-report",
    "client-intake",
  ])

  type        = "zip"
  source_dir  = "${path.module}/../../../lambdas/${each.key}"
  output_path = "${path.module}/../../../lambdas/${each.key}.zip"
}

# ─── Security Group for Lambdas ────────────────────────────────────

resource "aws_security_group" "lambda" {
  name        = "${local.name_prefix}-lambda-sg"
  description = "Security group for CloudGuard Lambda functions"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-lambda-sg"
  }
}

# ─── Injection Lambda ──────────────────────────────────────────────

resource "aws_lambda_function" "injection" {
  filename         = data.archive_file.lambda["injection"].output_path
  source_code_hash = data.archive_file.lambda["injection"].output_base64sha256
  function_name    = "${local.name_prefix}-injection"
  role             = var.injection_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 128

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      AWS_REGION          = var.aws_region
      FIS_EXPERIMENT_ID   = "" # Set after FIS module is applied
    }
  }
}

# ─── Monitor Lambda ────────────────────────────────────────────────

resource "aws_lambda_function" "monitor" {
  filename         = data.archive_file.lambda["monitor"].output_path
  source_code_hash = data.archive_file.lambda["monitor"].output_base64sha256
  function_name    = "${local.name_prefix}-monitor"
  role             = var.monitor_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 900
  memory_size      = 256

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT = var.environment
      AWS_REGION  = var.aws_region
    }
  }
}

# ─── Measurement Lambda ────────────────────────────────────────────

resource "aws_lambda_function" "measurement" {
  filename         = data.archive_file.lambda["measurement"].output_path
  source_code_hash = data.archive_file.lambda["measurement"].output_base64sha256
  function_name    = "${local.name_prefix}-measurement"
  role             = var.measurement_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT = var.environment
      AWS_REGION  = var.aws_region
    }
  }
}

# ─── Scoring Lambda ────────────────────────────────────────────────

resource "aws_lambda_function" "scoring" {
  filename         = data.archive_file.lambda["scoring"].output_path
  source_code_hash = data.archive_file.lambda["scoring"].output_base64sha256
  function_name    = "${local.name_prefix}-scoring"
  role             = var.scoring_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT              = var.environment
      AWS_REGION               = var.aws_region
      TEST_RUNS_TABLE          = var.test_runs_table_name
      RTO_TARGET_SSM_ARN       = var.rto_target_ssm_arn
      RPO_TARGET_SSM_ARN       = var.rpo_target_ssm_arn
      SCORE_THRESHOLD_SSM_ARN  = var.score_threshold_ssm_arn
    }
  }
}

# ─── Audit Report Lambda ───────────────────────────────────────────

resource "aws_lambda_function" "audit_report" {
  filename         = data.archive_file.lambda["audit-report"].output_path
  source_code_hash = data.archive_file.lambda["audit-report"].output_base64sha256
  function_name    = "${local.name_prefix}-audit-report"
  role             = var.audit_report_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      AWS_REGION           = var.aws_region
      REPORTS_BUCKET       = var.reports_bucket_id
      AUDIT_REPORTS_TABLE  = var.audit_reports_table_name
    }
  }
}

# ─── External Audit Lambda ─────────────────────────────────────────

resource "aws_lambda_function" "external_audit" {
  filename         = data.archive_file.lambda["external-audit"].output_path
  source_code_hash = data.archive_file.lambda["external-audit"].output_base64sha256
  function_name    = "${local.name_prefix}-external-audit"
  role             = var.external_audit_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      AWS_REGION           = var.aws_region
      REPORTS_BUCKET       = var.reports_bucket_id
      AUDIT_REPORTS_TABLE  = var.audit_reports_table_name
    }
  }
}

# ─── Alert Lambda ──────────────────────────────────────────────────

resource "aws_lambda_function" "alert" {
  filename         = data.archive_file.lambda["alert"].output_path
  source_code_hash = data.archive_file.lambda["alert"].output_base64sha256
  function_name    = "${local.name_prefix}-alert"
  role             = var.alert_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      AWS_REGION          = var.aws_region
      SNS_TOPIC_ARN       = var.sns_topic_arn
      TEST_RUNS_TABLE     = var.test_runs_table_name
      SCORE_THRESHOLD_SSM_ARN = var.score_threshold_ssm_arn
    }
  }
}

# ─── API Lambda ────────────────────────────────────────────────────

resource "aws_lambda_function" "api" {
  filename         = data.archive_file.lambda["api"].output_path
  source_code_hash = data.archive_file.lambda["api"].output_base64sha256
  function_name    = "${local.name_prefix}-api"
  role             = var.api_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT              = var.environment
      AWS_REGION               = var.aws_region
      TEST_RUNS_TABLE          = var.test_runs_table_name
      AUDIT_REPORTS_TABLE      = var.audit_reports_table_name
      REPORTS_BUCKET           = var.reports_bucket_id
    }
  }
}

# ─── Outputs ────────────────────────────────────────────────────────

output "injection_lambda_arn" {
  value = aws_lambda_function.injection.arn
}

output "monitor_lambda_arn" {
  value = aws_lambda_function.monitor.arn
}

output "measurement_lambda_arn" {
  value = aws_lambda_function.measurement.arn
}

output "scoring_lambda_arn" {
  value = aws_lambda_function.scoring.arn
}

output "audit_report_lambda_arn" {
  value = aws_lambda_function.audit_report.arn
}

output "external_audit_lambda_arn" {
  value = aws_lambda_function.external_audit.arn
}

output "alert_lambda_arn" {
  value = aws_lambda_function.alert.arn
}

output "api_lambda_invoke_arn" {
  value = aws_lambda_function.api.invoke_arn
}

output "external_audit_lambda_invoke_arn" {
  value = aws_lambda_function.external_audit.invoke_arn
}

output "api_lambda_function_name" {
  value = aws_lambda_function.api.function_name
}

# ─── SEO Report Lambda ─────────────────────────────────────────────

resource "aws_lambda_function" "seo_report" {
  filename         = data.archive_file.lambda["seo-report"].output_path
  source_code_hash = data.archive_file.lambda["seo-report"].output_base64sha256
  function_name    = "${local.name_prefix}-seo-report"
  role             = var.seo_report_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      AWS_REGION           = var.aws_region
      REPORTS_BUCKET       = var.reports_bucket_id
      AUDIT_REPORTS_TABLE  = var.audit_reports_table_name
    }
  }
}

output "seo_report_lambda_arn" {
  value = aws_lambda_function.seo_report.arn
}

output "seo_report_lambda_invoke_arn" {
  value = aws_lambda_function.seo_report.invoke_arn
}

output "seo_report_lambda_function_name" {
  value = aws_lambda_function.seo_report.function_name
}

# ─── Competitor Analysis Lambda ────────────────────────────────────

resource "aws_lambda_function" "competitor_analysis" {
  filename         = data.archive_file.lambda["competitor-analysis"].output_path
  source_code_hash = data.archive_file.lambda["competitor-analysis"].output_base64sha256
  function_name    = "${local.name_prefix}-competitor-analysis"
  role             = var.competitor_analysis_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 120
  memory_size      = 256

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      AWS_REGION           = var.aws_region
      REPORTS_BUCKET       = var.reports_bucket_id
      AUDIT_REPORTS_TABLE  = var.audit_reports_table_name
    }
  }
}

output "competitor_analysis_lambda_arn" {
  value = aws_lambda_function.competitor_analysis.arn
}

output "competitor_analysis_lambda_invoke_arn" {
  value = aws_lambda_function.competitor_analysis.invoke_arn
}

output "competitor_analysis_lambda_function_name" {
  value = aws_lambda_function.competitor_analysis.function_name
}

# ─── PDF Report Lambda ────────────────────────────────────────────

resource "aws_lambda_function" "pdf_report" {
  filename         = data.archive_file.lambda["pdf-report"].output_path
  source_code_hash = data.archive_file.lambda["pdf-report"].output_base64sha256
  function_name    = "${local.name_prefix}-pdf-report"
  role             = var.pdf_report_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 120
  memory_size      = 512
  layers           = var.pdf_report_layer_arn != "" ? [var.pdf_report_layer_arn] : []

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      AWS_REGION           = var.aws_region
      REPORTS_BUCKET       = var.reports_bucket_id
      AUDIT_REPORTS_TABLE  = var.audit_reports_table_name
    }
  }
}

output "pdf_report_lambda_arn" {
  value = aws_lambda_function.pdf_report.arn
}

output "pdf_report_lambda_invoke_arn" {
  value = aws_lambda_function.pdf_report.invoke_arn
}

output "pdf_report_lambda_function_name" {
  value = aws_lambda_function.pdf_report.function_name
}

# ─── Client Intake Lambda ──────────────────────────────────────────

resource "aws_lambda_function" "client_intake" {
  filename         = data.archive_file.lambda["client-intake"].output_path
  source_code_hash = data.archive_file.lambda["client-intake"].output_base64sha256
  function_name    = "${local.name_prefix}-client-intake"
  role             = var.client_intake_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT  = var.environment
      CLIENTS_TABLE = var.clients_table_name
    }
  }
}

output "client_intake_lambda_arn" {
  value = aws_lambda_function.client_intake.arn
}

output "client_intake_lambda_invoke_arn" {
  value = aws_lambda_function.client_intake.invoke_arn
}

output "client_intake_lambda_function_name" {
  value = aws_lambda_function.client_intake.function_name
}

output "external_audit_lambda_function_name" {
  value = aws_lambda_function.external_audit.function_name
}
