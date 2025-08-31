terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws    = { source = "hashicorp/aws", version = ">= 5.0" }
    random = { source = "hashicorp/random", version = ">= 3.5" }
  }
}

provider "aws" {
  region = var.aws_region
}

########################
# Variables
########################

variable "project_name"       { type = string, default = "interesting-chess" }
variable "aws_region"         { type = string, default = "us-east-1" }

# Data/config passed to the container/script
variable "contact_info"       { type = string }  # e.g., "Your Name <you@example.com>"
variable "titles"             { type = string,  default = "GM,WGM,IM,WIM,FM,WFM,NM,WNM,CM,WCM" }
variable "days_window"        { type = number,  default = 30 }
variable "request_sleep_s"    { type = number,  default = 0.25 }
variable "limit_players"      { type = number,  default = 0 }   # 0 = no limit

# Schedule: cron(5 3 * * ? *) == 03:05 UTC daily
variable "schedule_expression"{ type = string,  default = "cron(5 3 * * ? *)" }

# Optional CloudFront
variable "create_cloudfront"  { type = bool,    default = true }

# Path to your python file on local disk
variable "script_local_path"  { type = string,  default = "${path.module}/interesting_chess.py" }

locals {
  short         = replace(lower(var.project_name), "/[^a-z0-9-]/", "-")
  suffix        = random_id.sfx.hex
  bucket_name   = "${local.short}-data-${local.suffix}"
  latest_prefix = "latest"
  code_key      = "code/interesting_chess.py"
}

resource "random_id" "sfx" { byte_length = 3 }

########################
# S3 bucket (private)
########################

resource "aws_s3_bucket" "data" {
  bucket = local.bucket_name
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CORS so browser front-ends can fetch JSON
resource "aws_s3_bucket_cors_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  cors_rule {
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    allowed_headers = ["*"]
    max_age_seconds = 3600
  }
}

# Upload the Python script for the Batch job to download
resource "aws_s3_object" "script" {
  bucket = aws_s3_bucket.data.id
  key    = local.code_key
  source = var.script_local_path
  etag   = filemd5(var.script_local_path)
}

########################
# (Optional) CloudFront with OAC
########################

resource "aws_cloudfront_origin_access_control" "oac" {
  count                             = var.create_cloudfront ? 1 : 0
  name                              = "${local.short}-oac"
  description                       = "OAC for ${var.project_name} data"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "cdn" {
  count               = var.create_cloudfront ? 1 : 0
  enabled             = true
  default_root_object = ""

  origin {
    origin_id                = "s3-origin"
    domain_name              = aws_s3_bucket.data.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.oac[0].id
  }

  default_cache_behavior {
    target_origin_id       = "s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 300
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate { cloudfront_default_certificate = true }
}

# Bucket policy allowing only CloudFront (OAC) to read
resource "aws_s3_bucket_policy" "oac_read" {
  count  = var.create_cloudfront ? 1 : 0
  bucket = aws_s3_bucket.data.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Sid       = "AllowCloudFrontRead"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = ["s3:GetObject"]
      Resource  = "${aws_s3_bucket.data.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.cdn[0].arn
        }
      }
    }]
  })
}

########################
# VPC (default) + SG
########################

data "aws_vpc" "default" { default = true }
data "aws_subnets" "default" {
  filter { name = "vpc-id" ; values = [data.aws_vpc.default.id] }
}

resource "aws_security_group" "batch_instances" {
  name        = "${local.short}-batch-sg-${local.suffix}"
  description = "Egress-only for Batch EC2"
  vpc_id      = data.aws_vpc.default.id
  egress { from_port = 0, to_port = 0, protocol = "-1", cidr_blocks = ["0.0.0.0/0"] }
}

########################
# IAM
########################

# Batch service role
data "aws_iam_policy" "batch_service_managed" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

resource "aws_iam_role" "batch_service" {
  name               = "${local.short}-batch-svc-${local.suffix}"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{ Effect="Allow", Principal={ Service="batch.amazonaws.com" }, Action="sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy_attachment" "batch_service_attach" {
  role       = aws_iam_role.batch_service.name
  policy_arn = data.aws_iam_policy.batch_service_managed.arn
}

# ECS instance role/profile for Batch EC2
data "aws_iam_policy" "ecs_instance_managed" {
  arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}
data "aws_iam_policy" "ecr_readonly" {
  arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}
resource "aws_iam_role" "ecs_instance" {
  name               = "${local.short}-ecs-inst-${local.suffix}"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{ Effect="Allow", Principal={ Service="ec2.amazonaws.com" }, Action="sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy_attachment" "ecs_inst_attach1" {
  role       = aws_iam_role.ecs_instance.name
  policy_arn = data.aws_iam_policy.ecs_instance_managed.arn
}
resource "aws_iam_role_policy_attachment" "ecs_inst_attach2" {
  role       = aws_iam_role.ecs_instance.name
  policy_arn = data.aws_iam_policy.ecr_readonly.arn
}
resource "aws_iam_instance_profile" "ecs_instance_profile" {
  name = "${local.short}-ecs-prof-${local.suffix}"
  role = aws_iam_role.ecs_instance.name
}

# Job role (permissions used by the container to read code & write outputs)
resource "aws_iam_role" "job_role" {
  name               = "${local.short}-job-role-${local.suffix}"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{ Effect="Allow", Principal={ Service="ecs-tasks.amazonaws.com" }, Action="sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy" "job_role_policy" {
  role = aws_iam_role.job_role.id
  policy = jsonencode({
    Version="2012-10-17",
    Statement=[
      {
        Sid="ReadCode", Effect="Allow",
        Action=["s3:GetObject"],
        Resource="${aws_s3_bucket.data.arn}/${local.code_key}"
      },
      {
        Sid="WriteOutputs", Effect="Allow",
        Action=["s3:PutObject","s3:PutObjectAcl"],
        Resource="${aws_s3_bucket.data.arn}/${local.latest_prefix}/*"
      },
      {
        Sid="ListBucket", Effect="Allow",
        Action=["s3:ListBucket"],
        Resource=aws_s3_bucket.data.arn
      }
    ]
  })
}

# EventBridge -> Batch submit role
resource "aws_iam_role" "events_to_batch" {
  name               = "${local.short}-events-${local.suffix}"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{ Effect="Allow", Principal={ Service="events.amazonaws.com" }, Action="sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy" "events_to_batch_policy" {
  role = aws_iam_role.events_to_batch.id
  policy = jsonencode({
    Version="2012-10-17",
    Statement=[{
      Effect="Allow",
      Action=["batch:SubmitJob"],
      Resource=[aws_batch_job_queue.queue.arn, aws_batch_job_definition.job.arn]
    }]
  })
}

########################
# Batch: compute env, queue, job definition
########################

resource "aws_batch_compute_environment" "ec2" {
  compute_environment_name = "${local.short}-ec2-ce"
  type                     = "MANAGED"
  service_role             = aws_iam_role.batch_service.arn

  compute_resources {
    type                = "EC2"
    allocation_strategy = "BEST_FIT_PROGRESSIVE"
    min_vcpus           = 0
    desired_vcpus       = 0
    max_vcpus           = 1
    instance_role       = aws_iam_instance_profile.ecs_instance_profile.arn
    instance_types      = ["t2.micro","t3.micro"] # t2.micro is Free Tier–eligible; t3.micro as fallback
    subnets             = data.aws_subnets.default.ids
    security_group_ids  = [aws_security_group.batch_instances.id]
    tags = { Name = "${local.short}-batch-ec2" }
  }
}

resource "aws_batch_job_queue" "queue" {
  name     = "${local.short}-queue"
  state    = "ENABLED"
  priority = 1
  compute_environments = [aws_batch_compute_environment.ec2.arn]
}

resource "aws_batch_job_definition" "job" {
  name                   = "${local.short}-job"
  type                   = "container"
  platform_capabilities  = ["EC2"]

  container_properties = jsonencode({
    image       = "public.ecr.aws/docker/library/python:3.11-slim"
    vcpus       = 1
    memory      = 1024
    jobRoleArn  = aws_iam_role.job_role.arn
    environment = [
      { name = "IC_CONTACT",          value = var.contact_info },
      { name = "IC_TITLES",           value = var.titles },
      { name = "IC_DAYS",             value = tostring(var.days_window) },
      { name = "IC_SLEEP",            value = tostring(var.request_sleep_s) },
      { name = "IC_LIMIT_PLAYERS",    value = tostring(var.limit_players) },
      { name = "BUCKET",              value = aws_s3_bucket.data.bucket },
      { name = "PREFIX",              value = local.latest_prefix },
      { name = "SCRIPT_KEY",          value = local.code_key }
    ]
    command = [
      "bash","-lc", <<-EOC
        set -euo pipefail
        apt-get update -y && apt-get install -y --no-install-recommends awscli ca-certificates curl && rm -rf /var/lib/apt/lists/*
        python -m pip install --no-cache-dir --upgrade pip
        python -m pip install --no-cache-dir requests python-dateutil
        mkdir -p /app/out
        aws s3 cp "s3://$${BUCKET}/$${SCRIPT_KEY}" /app/interesting_chess.py
        chmod +x /app/interesting_chess.py
        python /app/interesting_chess.py --out /app/out
        aws s3 sync /app/out "s3://$${BUCKET}/$${PREFIX}" --delete
      EOC
    ]
  })
}

########################
# EventBridge Schedule -> Submit Batch Job
########################

resource "aws_cloudwatch_event_rule" "daily" {
  name                = "${local.short}-daily"
  description         = "Daily Interesting Chess data refresh"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "submit_job" {
  rule     = aws_cloudwatch_event_rule.daily.name
  arn      = aws_batch_job_queue.queue.arn   # IMPORTANT: target the Job Queue ARN
  role_arn = aws_iam_role.events_to_batch.arn
  batch_target {
    job_definition = aws_batch_job_definition.job.arn
    job_name       = "${local.short}-run"
    job_attempts   = 1
  }
}

########################
# Outputs
########################

output "s3_bucket_name" {
  value = aws_s3_bucket.data.bucket
}

output "cloudfront_domain" {
  value       = var.create_cloudfront ? aws_cloudfront_distribution.cdn[0].domain_name : ""
  description = "If enabled, fetch https://<domain>/${local.latest_prefix}/interesting_streaks.json"
}

output "batch_job_queue_arn" {
  value = aws_batch_job_queue.queue.arn
}

output "batch_job_definition_arn" {
  value = aws_batch_job_definition.job.arn
}
