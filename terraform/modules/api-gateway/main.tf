variable "environment" { type = string }
variable "cognito_user_pool_id" { type = string }
variable "cognito_client_id" { type = string }
variable "api_lambda_invoke_arn" { type = string }
variable "external_audit_lambda_invoke_arn" { type = string }
variable "api_lambda_function_name" { type = string }
variable "external_audit_lambda_function_name" { type = string }
variable "seo_report_lambda_invoke_arn" { type = string }
variable "seo_report_lambda_function_name" { type = string }
variable "competitor_analysis_lambda_invoke_arn" { type = string }
variable "competitor_analysis_lambda_function_name" { type = string }
variable "pdf_report_lambda_invoke_arn" { type = string }
variable "pdf_report_lambda_function_name" { type = string }
variable "client_intake_lambda_invoke_arn" { type = string }
variable "client_intake_lambda_function_name" { type = string }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── REST API ──────────────────────────────────────────────────────

resource "aws_api_gateway_rest_api" "main" {
  name = "${local.name_prefix}-api"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${local.name_prefix}-api"
  }
}

# ─── Cognito Authorizer ────────────────────────────────────────────

resource "aws_api_gateway_authorizer" "cognito" {
  name          = "${local.name_prefix}-cognito-authorizer"
  rest_api_id   = aws_api_gateway_rest_api.main.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = ["arn:aws:cognito-idp:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:userpool/${var.cognito_user_pool_id}"]
}

# ─── /runs Resource ────────────────────────────────────────────────

resource "aws_api_gateway_resource" "runs" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "runs"
}

# GET /runs
resource "aws_api_gateway_method" "runs_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.runs.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "runs_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.runs.id
  http_method             = aws_api_gateway_method.runs_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.api_lambda_invoke_arn
}

# ─── /runs/{run_id} Resource ──────────────────────────────────────

resource "aws_api_gateway_resource" "run_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.runs.id
  path_part   = "{run_id}"
}

# GET /runs/{run_id}
resource "aws_api_gateway_method" "run_id_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.run_id.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "run_id_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.run_id.id
  http_method             = aws_api_gateway_method.run_id_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.api_lambda_invoke_arn
}

# GET /runs/{run_id}/report
resource "aws_api_gateway_resource" "run_report" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.run_id.id
  path_part   = "report"
}

resource "aws_api_gateway_method" "run_report_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.run_report.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "run_report_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.run_report.id
  http_method             = aws_api_gateway_method.run_report_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.api_lambda_invoke_arn
}

# ─── /compare Resource ────────────────────────────────────────────

resource "aws_api_gateway_resource" "compare" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "compare"
}

# POST /compare
resource "aws_api_gateway_method" "compare_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.compare.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "compare_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.compare.id
  http_method             = aws_api_gateway_method.compare_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.api_lambda_invoke_arn
}

# ─── /audit/external Resource ─────────────────────────────────────

resource "aws_api_gateway_resource" "audit" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "audit"
}

resource "aws_api_gateway_resource" "audit_external" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.audit.id
  path_part   = "external"
}

# POST /audit/external
resource "aws_api_gateway_method" "audit_external_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.audit_external.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "audit_external_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.audit_external.id
  http_method             = aws_api_gateway_method.audit_external_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.external_audit_lambda_invoke_arn
}

# ─── /audit/seo Resource ─────────────────────────────────────────

resource "aws_api_gateway_resource" "audit_seo" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.audit.id
  path_part   = "seo"
}

# POST /audit/seo
resource "aws_api_gateway_method" "audit_seo_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.audit_seo.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "audit_seo_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.audit_seo.id
  http_method             = aws_api_gateway_method.audit_seo_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.seo_report_lambda_invoke_arn
}

# ─── /audit/competitors Resource ──────────────────────────────────

resource "aws_api_gateway_resource" "audit_competitors" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.audit.id
  path_part   = "competitors"
}

# POST /audit/competitors
resource "aws_api_gateway_method" "audit_competitors_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.audit_competitors.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "audit_competitors_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.audit_competitors.id
  http_method             = aws_api_gateway_method.audit_competitors_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.competitor_analysis_lambda_invoke_arn
}

# ─── /clients Resource ───────────────────────────────────────────

resource "aws_api_gateway_resource" "clients" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "clients"
}

# GET /clients
resource "aws_api_gateway_method" "clients_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.clients.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "clients_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.clients.id
  http_method             = aws_api_gateway_method.clients_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.client_intake_lambda_invoke_arn
}

# POST /clients
resource "aws_api_gateway_method" "clients_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.clients.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "clients_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.clients.id
  http_method             = aws_api_gateway_method.clients_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.client_intake_lambda_invoke_arn
}

# ─── /clients/{client_id} Resource ────────────────────────────────

resource "aws_api_gateway_resource" "client_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.clients.id
  path_part   = "{client_id}"
}

# GET /clients/{client_id}
resource "aws_api_gateway_method" "client_id_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.client_id.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "client_id_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.client_id.id
  http_method             = aws_api_gateway_method.client_id_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.client_intake_lambda_invoke_arn
}

# ─── /report/pdf Resource ────────────────────────────────────────

resource "aws_api_gateway_resource" "report" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "report"
}

resource "aws_api_gateway_resource" "report_pdf" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.report.id
  path_part   = "pdf"
}

# POST /report/pdf
resource "aws_api_gateway_method" "report_pdf_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.report_pdf.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "report_pdf_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.report_pdf.id
  http_method             = aws_api_gateway_method.report_pdf_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.pdf_report_lambda_invoke_arn
}

# ─── /health Resource (No Auth) ───────────────────────────────────

resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "health"
}

resource "aws_api_gateway_method" "health_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "health_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.health.id
  http_method             = aws_api_gateway_method.health_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.api_lambda_invoke_arn
}

# ─── Deployment ────────────────────────────────────────────────────

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  depends_on = [
    aws_api_gateway_integration.runs_get,
    aws_api_gateway_integration.run_id_get,
    aws_api_gateway_integration.run_report_get,
    aws_api_gateway_integration.compare_post,
    aws_api_gateway_integration.audit_external_post,
    aws_api_gateway_integration.health_get,
    aws_api_gateway_integration.audit_seo_post,
    aws_api_gateway_integration.audit_competitors_post,
    aws_api_gateway_integration.report_pdf_post,
    aws_api_gateway_integration.clients_get,
    aws_api_gateway_integration.clients_post,
    aws_api_gateway_integration.client_id_get,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "prod"

  tags = {
    Name = "${local.name_prefix}-api-prod"
  }
}

# ─── Lambda Permission for API Gateway ────────────────────────────

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.api_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_external_audit" {
  statement_id  = "AllowAPIGatewayInvokeExternalAudit"
  action        = "lambda:InvokeFunction"
  function_name = var.external_audit_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# ─── CORS ──────────────────────────────────────────────────────────

resource "aws_api_gateway_method" "options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_rest_api.main.root_resource_id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_rest_api.main.root_resource_id
  http_method = aws_api_gateway_method.options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# ─── Outputs ────────────────────────────────────────────────────────

output "api_url" {
  value = aws_api_gateway_stage.prod.invoke_url
}

resource "aws_lambda_permission" "api_gateway_seo_report" {
  statement_id  = "AllowAPIGatewayInvokeSEOReport"
  action        = "lambda:InvokeFunction"
  function_name = var.seo_report_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_competitor_analysis" {
  statement_id  = "AllowAPIGatewayInvokeCompetitorAnalysis"
  action        = "lambda:InvokeFunction"
  function_name = var.competitor_analysis_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_client_intake" {
  statement_id  = "AllowAPIGatewayInvokeClientIntake"
  action        = "lambda:InvokeFunction"
  function_name = var.client_intake_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_pdf_report" {
  statement_id  = "AllowAPIGatewayInvokePDFReport"
  action        = "lambda:InvokeFunction"
  function_name = var.pdf_report_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

output "api_id" {
  value = aws_api_gateway_rest_api.main.id
}

# ─── Data Sources ──────────────────────────────────────────────────

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
