########################
# Batch: compute env, queue, job definition
########################

resource "aws_batch_compute_environment" "ec2" {
  # compute_environment_name is not supported in newer provider versions
  name         = "${local.short}-ec2-ce"
  type         = "MANAGED"
  service_role = aws_iam_role.batch_service.arn

  compute_resources {
    type                = "EC2"
    allocation_strategy = "BEST_FIT_PROGRESSIVE"
    min_vcpus           = 0
    desired_vcpus       = 0
    max_vcpus           = 1
    instance_role       = aws_iam_instance_profile.ecs_instance_profile.arn
    instance_type      = ["t3.micro"]
    subnets             = data.aws_subnets.default.ids
    security_group_ids  = [aws_security_group.batch_instances.id]
    tags                = { Name = "${local.short}-batch-ec2" }
  }
}

resource "aws_batch_job_queue" "queue" {
  name     = "${local.short}-queue"
  state    = "ENABLED"
  priority = 1
  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.ec2.arn
  }
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
      { name = "APP_NAME",            value = var.app_name },
      { name = "VERSION",             value = var.app_version },
      { name = "USERNAME",            value = var.username },
      { name = "EMAIL",               value = var.email },
      { name = "BUCKET",              value = aws_s3_bucket.data.bucket },
      { name = "PREFIX",              value = local.latest_prefix },
      { name = "CODE_PREFIX",         value = local.code_prefix },
      { name = "S3_LOCATION",         value = "s3://${aws_s3_bucket.data.bucket}/${local.latest_prefix}/" },
      { name = "AWS_ACCESS_KEY_ID",   value = aws_iam_access_key.batch_user_key.id },
      { name = "AWS_SECRET_ACCESS_KEY", value = aws_iam_access_key.batch_user_key.secret },
      { name = "AWS_REGION",  value = var.aws_region },
      { name = "AWS_DEFAULT_REGION",  value = var.aws_region }
    ]
    command = [
      "bash","-lc", <<-EOC
        set -euo pipefail
        apt-get update -y && apt-get install -y --no-install-recommends awscli ca-certificates curl unzip && rm -rf /var/lib/apt/lists/*
        python -m pip install --no-cache-dir --upgrade pip
        python -m pip install --no-cache-dir requests python-dateutil chess.com boto3
        mkdir -p /app/scraping /app/out
        aws s3 cp "s3://$${BUCKET}/$${CODE_PREFIX}/scraping.zip" /app/scraping.zip
        cd /app && unzip scraping.zip -d scraping/
        cd /app/scraping
        python main.py --days ${var.days_window} --out /app/out --titles "${var.titles}" ${ var.limit_players > 0 ? "--limit-players ${var.limit_players}" : ""} --verbose
      EOC
    ]
  })
}
