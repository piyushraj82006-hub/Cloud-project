variable "environment" { type = string }
variable "injection_lambda_arn" { type = string }
variable "monitor_lambda_arn" { type = string }
variable "measurement_lambda_arn" { type = string }
variable "scoring_lambda_arn" { type = string }
variable "audit_report_lambda_arn" { type = string }
variable "ai_insights_lambda_arn" { type = string }
variable "pdf_report_lambda_arn" { type = string }
variable "alert_lambda_arn" { type = string }
variable "step_functions_role_arn" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

resource "aws_sfn_state_machine" "dr_test" {
  name     = "${local.name_prefix}-dr-test"
  role_arn = var.step_functions_role_arn

  definition = jsonencode({
    Comment = "CloudGuard DR Test: Inject → Monitor → Measure → Score → Report → AIInsights → GeneratePDF → Alert"
    StartAt = "Inject"
    States = {
      Inject = {
        Type     = "Task"
        Resource = var.injection_lambda_arn
        Next     = "Monitor"
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "Failed"
          }
        ]
      }

      Monitor = {
        Type     = "Task"
        Resource = var.monitor_lambda_arn
        Next     = "Measure"
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 10
            MaxAttempts     = 2
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "Failed"
          }
        ]
      }

      Measure = {
        Type     = "Task"
        Resource = var.measurement_lambda_arn
        Next     = "Score"
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "Failed"
          }
        ]
      }

      Score = {
        Type     = "Task"
        Resource = var.scoring_lambda_arn
        Next     = "Report"
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "Failed"
          }
        ]
      }

      Report = {
        Type     = "Task"
        Resource = var.audit_report_lambda_arn
        Next     = "AIInsights"
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "Failed"
          }
        ]
      }

      AIInsights = {
        Type     = "Task"
        Resource = var.ai_insights_lambda_arn
        Next     = "GeneratePDF"
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 10
            MaxAttempts     = 1
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "GeneratePDF"
            ResultPath  = "$.ai_error"
          }
        ]
      }

      GeneratePDF = {
        Type      = "Task"
        Resource  = var.pdf_report_lambda_arn
        InputPath = "$"
        Parameters = {
          "report_type" = "dr-test"
          "report_id."  = "$.run_id"
          "agency_name" = "CloudGuard DR"
        }
        Next = "Alert"
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 10
            MaxAttempts     = 2
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "Alert"
            ResultPath  = "$.pdf_error"
          }
        ]
      }

      Alert = {
        Type     = "Task"
        Resource = var.alert_lambda_arn
        Next     = "Success"
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "Failed"
          }
        ]
      }

      Success = {
        Type = "Succeed"
      }

      Failed = {
        Type  = "Fail"
        Cause = "Test run failed"
        Error = "DRTestFailed"
      }
    }
  })

  tags = {
    Name = "${local.name_prefix}-dr-test"
  }
}

output "state_machine_arn" {
  value = aws_sfn_state_machine.dr_test.arn
}

output "state_machine_name" {
  value = aws_sfn_state_machine.dr_test.name
}
