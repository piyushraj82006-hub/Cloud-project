variable "environment" { type = string }
variable "step_functions_arn" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── Weekly Test Schedule ──────────────────────────────────────────

resource "aws_cloudwatch_event_rule" "weekly_test" {
  name                = "${local.name_prefix}-weekly-test"
  description         = "Trigger CloudGuard DR test every Monday at 8 AM UTC"
  schedule_expression = "cron(0 8 ? * MON *)"

  tags = {
    Name = "${local.name_prefix}-weekly-test"
  }
}

resource "aws_cloudwatch_event_target" "step_functions" {
  rule     = aws_cloudwatch_event_rule.weekly_test.name
  arn      = var.step_functions_arn
  role_arn = ""

  input = jsonencode({
    fault_type     = "ec2-termination"
    target_resource = "auto"
  })
}

output "rule_arn" {
  value = aws_cloudwatch_event_rule.weekly_test.arn
}

output "rule_name" {
  value = aws_cloudwatch_event_rule.weekly_test.name
}
