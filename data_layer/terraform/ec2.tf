########################
# ECS Fargate: cluster, task definition, log group
########################

locals {
  # build the optional CLI arg for limiting players so the long jsonencode string stays readable
  limit_players_arg = var.limit_players > 0 ? "--limit-players ${var.limit_players}" : ""
}

resource "aws_ecs_cluster" "main" {
  name = "${local.short}-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name = "${local.short}-ecs-cluster"
  }
}

resource "aws_ecs_task_definition" "chess_scraper" {
  family                   = "${local.short}-chess-scraper"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = 256  # 0.25 vCPU - very cost effective
  memory                  = 1024 # 1GB RAM as requested
  execution_role_arn      = aws_iam_role.ecs_execution_role.arn
  task_role_arn          = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "chess-scraper"
      image = "public.ecr.aws/docker/library/python:3.11-slim"
      
      environment = [
        { name = "APP_NAME", value = var.app_name },
        { name = "VERSION", value = var.app_version },
        { name = "USERNAME", value = var.username },
        { name = "EMAIL", value = var.email },
        { name = "BUCKET", value = aws_s3_bucket.data.bucket },
        { name = "CODE_BUCKET", value = aws_s3_bucket.code.bucket },
        { name = "PREFIX", value = local.latest_prefix },
        { name = "CODE_PREFIX", value = local.code_prefix },
        { name = "S3_LOCATION", value = "s3://${aws_s3_bucket.data.bucket}/${local.latest_prefix}/" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region }
      ]
      
      command = [
        "bash", "-c",
        join(" && ", [
          "set -eu",
          "apt-get update -y",
          "apt-get install -y --no-install-recommends awscli ca-certificates curl unzip",
          "rm -rf /var/lib/apt/lists/*",
          "python -m pip install --no-cache-dir --upgrade pip",
          "mkdir -p /app/scraping /app/out",
          "aws s3 cp \"s3://$${CODE_BUCKET}/$${CODE_PREFIX}/scraping.zip\" /app/scraping.zip",
          "cd /app && unzip /app/scraping.zip -d scraping/",
          "cd /app/scraping && python -m pip install --no-cache-dir -r requirements.txt",
          "python main.py --days ${var.days_window} --out /app/out --titles \"${var.titles}\" ${local.limit_players_arg} --verbose"
        ])
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.chess_scraper.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      stopTimeout = 5
    }
  ])
  
  tags = {
    Name = "${local.short}-task-definition"
  }
}

resource "aws_cloudwatch_log_group" "chess_scraper" {
  name              = "/ecs/${local.short}-chess-scraper"
  retention_in_days = 14
  
  tags = {
    Name = "${local.short}-log-group"
  }
}

# Security group for ECS tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${local.short}-ecs-tasks"
  description = "Security group for ECS Fargate tasks"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.short}-ecs-tasks-sg"
  }
}
