variable "environment" { type = string }
variable "account_id" { type = string }

locals {
  name_prefix    = "cloudguard-${var.environment}"
  reports_bucket = "${local.name_prefix}-reports-${var.account_id}"
  dashboard_bucket = "${local.name_prefix}-dashboard-${var.account_id}"
}

# ─── Reports Bucket (Private) ──────────────────────────────────────

resource "aws_s3_bucket" "reports" {
  bucket = local.reports_bucket

  tags = {
    Name = "${local.name_prefix}-reports"
  }
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ─── Dashboard Bucket (Public Read for Static Assets) ──────────────

resource "aws_s3_bucket" "dashboard" {
  bucket = local.dashboard_bucket

  tags = {
    Name = "${local.name_prefix}-dashboard"
  }
}

resource "aws_s3_bucket_public_access_block" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_policy" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadForStaticAssets"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.dashboard.arn}/*"
      }
    ]
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ─── Outputs ────────────────────────────────────────────────────────

output "reports_bucket_id" {
  value = aws_s3_bucket.reports.id
}

output "reports_bucket_arn" {
  value = aws_s3_bucket.reports.arn
}

output "dashboard_bucket_id" {
  value = aws_s3_bucket.dashboard.id
}

output "dashboard_bucket_arn" {
  value = aws_s3_bucket.dashboard.arn
}

output "dashboard_website_endpoint" {
  value = aws_s3_bucket_website_configuration.dashboard.website_endpoint
}
