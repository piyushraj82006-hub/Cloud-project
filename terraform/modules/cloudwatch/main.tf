variable "environment" { type = string }
variable "step_functions_name" { type = string }
variable "sns_topic_arn" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── Step Functions Failure Alarm ──────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "step_functions_failure" {
  alarm_name          = "${local.name_prefix}-step-functions-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when any Step Functions execution fails"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    StateMachineArn = var.step_functions_name
  }

  tags = {
    Name = "${local.name_prefix}-sf-failure-alarm"
  }
}

# ─── Log Groups ────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "injection" {
  name              = "/aws/lambda/${local.name_prefix}-injection"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "monitor" {
  name              = "/aws/lambda/${local.name_prefix}-monitor"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "measurement" {
  name              = "/aws/lambda/${local.name_prefix}-measurement"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "scoring" {
  name              = "/aws/lambda/${local.name_prefix}-scoring"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "audit_report" {
  name              = "/aws/lambda/${local.name_prefix}-audit-report"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "external_audit" {
  name              = "/aws/lambda/${local.name_prefix}-external-audit"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "alert" {
  name              = "/aws/lambda/${local.name_prefix}-alert"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${local.name_prefix}-api"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "seo_report" {
  name              = "/aws/lambda/${local.name_prefix}-seo-report"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "competitor_analysis" {
  name              = "/aws/lambda/${local.name_prefix}-competitor-analysis"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "pdf_report" {
  name              = "/aws/lambda/${local.name_prefix}-pdf-report"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "client_intake" {
  name              = "/aws/lambda/${local.name_prefix}-client-intake"
  retention_in_days = 14
}
