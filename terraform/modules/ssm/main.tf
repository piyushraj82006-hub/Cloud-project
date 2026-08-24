variable "environment" { type = string }
variable "rto_target" { type = number }
variable "rpo_target" { type = number }
variable "score_threshold" { type = number }
variable "sns_topic_arn" { type = string }
variable "test_runs_table" { type = string }
variable "audit_reports_table" { type = string }
variable "reports_bucket" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

resource "aws_ssm_parameter" "rto_target" {
  name  = "/${local.name_prefix}/rto-target-seconds"
  type  = "String"
  value = tostring(var.rto_target)
}

resource "aws_ssm_parameter" "rpo_target" {
  name  = "/${local.name_prefix}/rpo-target-seconds"
  type  = "String"
  value = tostring(var.rpo_target)
}

resource "aws_ssm_parameter" "score_threshold" {
  name  = "/${local.name_prefix}/score-threshold"
  type  = "String"
  value = tostring(var.score_threshold)
}

resource "aws_ssm_parameter" "sns_topic_arn" {
  name  = "/${local.name_prefix}/sns-topic-arn"
  type  = "String"
  value = var.sns_topic_arn
}

resource "aws_ssm_parameter" "test_runs_table" {
  name  = "/${local.name_prefix}/test-runs-table"
  type  = "String"
  value = var.test_runs_table
}

resource "aws_ssm_parameter" "audit_reports_table" {
  name  = "/${local.name_prefix}/audit-reports-table"
  type  = "String"
  value = var.audit_reports_table
}

resource "aws_ssm_parameter" "reports_bucket" {
  name  = "/${local.name_prefix}/reports-bucket"
  type  = "String"
  value = var.reports_bucket
}

# ─── Outputs ────────────────────────────────────────────────────────

output "rto_target_arn" {
  value = aws_ssm_parameter.rto_target.arn
}

output "rpo_target_arn" {
  value = aws_ssm_parameter.rpo_target.arn
}

output "score_threshold_arn" {
  value = aws_ssm_parameter.score_threshold.arn
}

output "sns_topic_arn" {
  value = aws_ssm_parameter.sns_topic_arn.arn
}
