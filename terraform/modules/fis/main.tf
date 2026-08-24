variable "environment" { type = string }
variable "fis_role_arn" { type = string }
variable "sample_instance_ids" {
  type        = list(string)
  description = "List of EC2 instance IDs tagged for DR testing"
}

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── FIS Experiment Template ───────────────────────────────────────

resource "aws_fis_experiment_template" "instance_termination" {
  description = "Terminate an EC2 instance to test disaster recovery"

  role_arn = var.fis_role_arn

  stop_condition {
    source = "aws:cloudwatch:alarm"
    value  = ""
  }

  action {
    name      = "terminate-instance"
    action_id = "aws:ec2:terminate-instances"

    target {
      key   = "Instances"
      value = "dr-test-instances"
    }
  }

  target {
    name           = "dr-test-instances"
    resource_type  = "aws:ec2:instance"
    selection_mode = "ALL"
    resource_tag {
      key   = "dr-test"
      value = "true"
    }
  }

  log_configuration {
    cloudwatch_logs_configuration {
      log_group_arn = ""
    }
    log_configuration {
      s3_configuration {
        bucket_name = ""
        prefix      = "fis-logs"
      }
    }
  }

  tags = {
    Name = "${local.name_prefix}-fis-instance-termination"
  }
}

# ─── CloudWatch Alarm for FIS Stop Condition ──────────────────────

resource "aws_cloudwatch_metric_alarm" "fis_stop" {
  alarm_name          = "${local.name_prefix}-fis-stop-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 90
  alarm_description   = "Stop FIS experiment if CPU > 90%"

  tags = {
    Name = "${local.name_prefix}-fis-stop"
  }
}

output "experiment_template_id" {
  value = aws_fis_experiment_template.instance_termination.id
}
