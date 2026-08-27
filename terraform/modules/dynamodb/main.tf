variable "environment" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── TestRuns Table ─────────────────────────────────────────────────

resource "aws_dynamodb_table" "test_runs" {
  name         = "${local.name_prefix}-test-runs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_id"

  attribute {
    name = "run_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "timestamp-index"
    hash_key        = "timestamp"
    range_key       = "run_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.name_prefix}-test-runs"
  }
}

# ─── AuditReports Table ────────────────────────────────────────────

resource "aws_dynamodb_table" "audit_reports" {
  name         = "${local.name_prefix}-audit-reports"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "report_id"

  attribute {
    name = "report_id"
    type = "S"
  }

  attribute {
    name = "run_id"
    type = "S"
  }

  global_secondary_index {
    name            = "run_id-index"
    hash_key        = "run_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.name_prefix}-audit-reports"
  }
}

# ─── Outputs ────────────────────────────────────────────────────────

output "test_runs_table_name" {
  value = aws_dynamodb_table.test_runs.name
}

output "test_runs_table_arn" {
  value = aws_dynamodb_table.test_runs.arn
}

output "audit_reports_table_name" {
  value = aws_dynamodb_table.audit_reports.name
}

output "audit_reports_table_arn" {
  value = aws_dynamodb_table.audit_reports.arn
}

# ─── Clients Table ─────────────────────────────────────────────────

resource "aws_dynamodb_table" "clients" {
  name         = "${local.name_prefix}-clients"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "client_id"

  attribute {
    name = "client_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "created_at-index"
    hash_key        = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.name_prefix}-clients"
  }
}

output "clients_table_name" {
  value = aws_dynamodb_table.clients.name
}

output "clients_table_arn" {
  value = aws_dynamodb_table.clients.arn
}

# ─── Comparisons Table ─────────────────────────────────────────────

resource "aws_dynamodb_table" "comparisons" {
  name         = "${local.name_prefix}-comparisons"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "comparison_id"

  attribute {
    name = "comparison_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "created_at-index"
    hash_key        = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.name_prefix}-comparisons"
  }
}

output "comparisons_table_name" {
  value = aws_dynamodb_table.comparisons.name
}

output "comparisons_table_arn" {
  value = aws_dynamodb_table.comparisons.arn
}
