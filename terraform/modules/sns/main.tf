variable "environment" { type = string }
variable "admin_email" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"

  tags = {
    Name = "${local.name_prefix}-alerts"
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.admin_email
}

output "alert_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "alert_topic_name" {
  value = aws_sns_topic.alerts.name
}
