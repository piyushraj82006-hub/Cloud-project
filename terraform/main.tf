terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment for remote state
  # backend "s3" {
  #   bucket         = "cloudguard-terraform-state"
  #   key            = "dr-testing/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "CloudGuardDR"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ─── Variables ──────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev/demo)"
  type        = string
  default     = "dev"
}

variable "admin_email" {
  description = "Admin email for Cognito and SNS alerts"
  type        = string
}

variable "rto_target_seconds" {
  description = "Recovery Time Objective target in seconds"
  type        = number
  default     = 300
}

variable "rpo_target_seconds" {
  description = "Recovery Point Objective target in seconds"
  type        = number
  default     = 60
}

variable "score_threshold" {
  description = "Minimum resilience score to pass"
  type        = number
  default     = 70
}

# ─── Module Calls ───────────────────────────────────────────────────

module "network" {
  source = "./modules/network"

  environment = var.environment
}

module "iam" {
  source = "./modules/iam"

  environment      = var.environment
  aws_region       = var.aws_region
  account_id       = data.aws_caller_identity.current.account_id
  lambda_s3_bucket = module.s3.reports_bucket_id
}

module "dynamodb" {
  source = "./modules/dynamodb"

  environment = var.environment
}

module "s3" {
  source = "./modules/s3"

  environment = var.environment
  account_id  = data.aws_caller_identity.current.account_id
}

module "cognito" {
  source = "./modules/cognito"

  environment = var.environment
  admin_email = var.admin_email
}

module "sns" {
  source = "./modules/sns"

  environment = var.environment
  admin_email = var.admin_email
}

module "fis" {
  source = "./modules/fis"

  environment     = var.environment
  fis_role_arn    = module.iam.fis_execution_role_arn
  sample_instance_ids = module.sample_app.instance_ids
}

module "step_functions" {
  source = "./modules/step-functions"

  environment            = var.environment
  injection_lambda_arn   = module.lambda.injection_lambda_arn
  monitor_lambda_arn     = module.lambda.monitor_lambda_arn
  measurement_lambda_arn = module.lambda.measurement_lambda_arn
  scoring_lambda_arn     = module.lambda.scoring_lambda_arn
  audit_report_lambda_arn = module.lambda.audit_report_lambda_arn
  alert_lambda_arn       = module.lambda.alert_lambda_arn
  step_functions_role_arn = module.iam.step_functions_role_arn
}

module "sample_app" {
  source = "./modules/sample-app"

  environment = var.environment
  vpc_id      = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
}

module "lambda" {
  source = "./modules/lambda"

  environment         = var.environment
  aws_region          = var.aws_region
  account_id          = data.aws_caller_identity.current.account_id
  vpc_id              = module.network.vpc_id
  private_subnet_ids  = module.network.private_subnet_ids

  # IAM role ARNs
  injection_role_arn   = module.iam.injection_lambda_role_arn
  monitor_role_arn     = module.iam.monitor_lambda_role_arn
  measurement_role_arn = module.iam.measurement_lambda_role_arn
  scoring_role_arn     = module.iam.scoring_lambda_role_arn
  audit_report_role_arn = module.iam.audit_report_lambda_role_arn
  external_audit_role_arn = module.iam.external_audit_lambda_role_arn
  alert_role_arn       = module.iam.alert_lambda_role_arn
  api_role_arn         = module.iam.api_lambda_role_arn
  seo_report_role_arn  = module.iam.seo_report_lambda_role_arn
  competitor_analysis_role_arn = module.iam.competitor_analysis_lambda_role_arn
  pdf_report_role_arn         = module.iam.pdf_report_lambda_role_arn
  client_intake_role_arn      = module.iam.client_intake_lambda_role_arn

  # DynamoDB
  test_runs_table_name      = module.dynamodb.test_runs_table_name
  audit_reports_table_name  = module.dynamodb.audit_reports_table_name
  clients_table_name        = module.dynamodb.clients_table_name

  # S3
  reports_bucket_id = module.s3.reports_bucket_id

  # SNS
  sns_topic_arn = module.sns.alert_topic_arn

  # SSM Parameters
  rto_target_ssm_arn  = module.ssm.rto_target_arn
  rpo_target_ssm_arn  = module.ssm.rpo_target_arn
  score_threshold_ssm_arn = module.ssm.score_threshold_arn
  sns_topic_ssm_arn   = module.ssm.sns_topic_arn
}

module "api_gateway" {
  source = "./modules/api-gateway"

  environment        = var.environment
  cognito_user_pool_id = module.cognito.user_pool_id
  cognito_client_id    = module.cognito.client_id

  api_lambda_invoke_arn        = module.lambda.api_lambda_invoke_arn
  external_audit_lambda_invoke_arn = module.lambda.external_audit_lambda_invoke_arn
  seo_report_lambda_invoke_arn     = module.lambda.seo_report_lambda_invoke_arn
  competitor_analysis_lambda_invoke_arn = module.lambda.competitor_analysis_lambda_invoke_arn
  pdf_report_lambda_invoke_arn          = module.lambda.pdf_report_lambda_invoke_arn
  client_intake_lambda_invoke_arn       = module.lambda.client_intake_lambda_invoke_arn
  api_lambda_function_name     = module.lambda.api_lambda_function_name
  external_audit_lambda_function_name = module.lambda.external_audit_lambda_function_name
  seo_report_lambda_function_name     = module.lambda.seo_report_lambda_function_name
  competitor_analysis_lambda_function_name = module.lambda.competitor_analysis_lambda_function_name
  pdf_report_lambda_function_name          = module.lambda.pdf_report_lambda_function_name
  client_intake_lambda_function_name       = module.lambda.client_intake_lambda_function_name
}

module "ssm" {
  source = "./modules/ssm"

  environment      = var.environment
  rto_target       = var.rto_target_seconds
  rpo_target       = var.rpo_target_seconds
  score_threshold  = var.score_threshold
  sns_topic_arn    = module.sns.alert_topic_arn
  test_runs_table  = module.dynamodb.test_runs_table_name
  audit_reports_table = module.dynamodb.audit_reports_table_name
  reports_bucket   = module.s3.reports_bucket_id
}

module "eventbridge" {
  source = "./modules/eventbridge"

  environment          = var.environment
  step_functions_arn   = module.step_functions.state_machine_arn
}

module "cloudwatch" {
  source = "./modules/cloudwatch"

  environment            = var.environment
  step_functions_name    = module.step_functions.state_machine_name
  sns_topic_arn          = module.sns.alert_topic_arn
}
