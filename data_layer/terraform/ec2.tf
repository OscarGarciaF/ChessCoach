########################
# ECS: cluster, task definition, log group
########################

locals {
  # build the optional CLI arg for limiting players so the long jsonencode string stays readable
  limit_players_arg = var.limit_players > 0 ? "--limit-players ${var.limit_players}" : ""
  # preferred instances in order of cost effectiveness (x86_64 only for compatibility)
  preferred_instances = ["t3a.nano", "t3.nano", "t2.nano", "t3a.micro", "t3.micro", "t2.micro"]
  /*
  on demand instances cost per hour (x86_64 instances only)
  t3a.nano: $0.0047
  t3.nano: 	$0.0052
  t2.nano: $0.0058
  t3a.micro: $0.0094
  t3.micro: $0.0104
  t2.micro: $0.0116
  
  Note: t4g instances (ARM64) removed for architecture consistency
  t4g.nano: $0.0042 (cheapest but ARM64)
  t4g.micro: $0.0084 (ARM64)
  */
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

# Capacity provider for the ECS cluster
resource "aws_ecs_capacity_provider" "main" {
  name = "${local.short}-capacity-provider"

  auto_scaling_group_provider {
    auto_scaling_group_arn         = aws_autoscaling_group.ecs.arn
    managed_termination_protection = "DISABLED"

    managed_scaling {
      maximum_scaling_step_size = 1
      minimum_scaling_step_size = 1
      status                    = "ENABLED"
      target_capacity           = 100
    }
  }

  tags = {
    Name = "${local.short}-capacity-provider"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = [aws_ecs_capacity_provider.main.name]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = aws_ecs_capacity_provider.main.name
  }
}

# Get the latest ECS-optimized AMI
data "aws_ami" "ecs_optimized" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-ecs-hvm-*-x86_64-ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get on-demand pricing for spot bid
data "aws_ec2_instance_type_offering" "preferred" {
  filter {
    name   = "instance-type"
    values = [local.preferred_instances[0]]
  }

  filter {
    name   = "location"
    values = [var.aws_region]
  }

  location_type = "region"
}

# Launch template for ECS instances
resource "aws_launch_template" "ecs_instance" {
  name_prefix   = "${local.short}-ecs-instance-"
  image_id      = data.aws_ami.ecs_optimized.id
  instance_type = local.preferred_instances[0]

  vpc_security_group_ids = [aws_security_group.ecs_instances.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.ecs_instance.name
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    echo ECS_CLUSTER=${aws_ecs_cluster.main.name} >> /etc/ecs/ecs.config
    echo ECS_ENABLE_SPOT_INSTANCE_DRAINING=true >> /etc/ecs/ecs.config
  EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${local.short}-ecs-instance"
    }
  }
}

# Auto Scaling Group for ECS instances
resource "aws_autoscaling_group" "ecs" {
  name                = "${local.short}-ecs-asg"
  vpc_zone_identifier = data.aws_subnets.default.ids
  target_group_arns   = []
  health_check_type   = "EC2"

  min_size         = 0
  max_size         = 2
  desired_capacity = 1

  # Use mixed instances policy to prefer spot instances
  mixed_instances_policy {
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.ecs_instance.id
        version            = "$Latest"
      }

      # Try multiple instance types in order of preference
      dynamic "override" {
        for_each = local.preferred_instances
        content {
          instance_type = override.value
        }
      }
    }

    instances_distribution {
      on_demand_base_capacity                  = 0
      on_demand_percentage_above_base_capacity = 0
      spot_allocation_strategy                 = "price-capacity-optimized"
      spot_max_price                           = "" # Use on-demand price as max
    }
  }

  tag {
    key                 = "AmazonECSManaged"
    value               = true
    propagate_at_launch = false
  }

  tag {
    key                 = "Name"
    value               = "${local.short}-ecs-asg"
    propagate_at_launch = false
  }
}

resource "aws_ecs_task_definition" "chess_scraper" {
  family                   = "${local.short}-chess-scraper"
  requires_compatibilities = ["EC2"]
  network_mode             = "bridge"
  cpu                      = 256 # 0.25 vCPU - very cost effective
  memory                   = 512 # 512MB RAM (reduced for EC2 efficiency)
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

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
          "python main.py"
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

# Security group for ECS tasks (bridge network mode)
resource "aws_security_group" "ecs_tasks" {
  name        = "${local.short}-ecs-tasks"
  description = "Security group for ECS EC2 tasks"
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

# Security group for ECS instances
resource "aws_security_group" "ecs_instances" {
  name        = "${local.short}-ecs-instances"
  description = "Security group for ECS EC2 instances"
  vpc_id      = data.aws_vpc.default.id

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow SSH access (optional, for debugging)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.short}-ecs-instances-sg"
  }
}
