variable "environment" { type = string }
variable "admin_email" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── User Pool ─────────────────────────────────────────────────────

resource "aws_cognito_user_pool" "main" {
  name = "${local.name_prefix}-users"

  username_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }

  auto_verified_attributes = ["email"]

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  tags = {
    Name = "${local.name_prefix}-user-pool"
  }
}

# ─── Admin User ────────────────────────────────────────────────────

resource "aws_cognito_user_pool_client" "dashboard" {
  name         = "${local.name_prefix}-dashboard-client"
  user_pool_id = aws_cognito_user_pool.main.id

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 30

  generate_secret = false
}

# ─── User Pool Domain ─────────────────────────────────────────────

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${local.name_prefix}-${substr(md5(terraform.workspace), 0, 6)}"
  user_pool_id = aws_cognito_user_pool.main.id
}

# ─── Outputs ────────────────────────────────────────────────────────

output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "client_id" {
  value = aws_cognito_user_pool_client.dashboard.id
}

output "domain" {
  value = aws_cognito_user_pool_domain.main.domain
}
