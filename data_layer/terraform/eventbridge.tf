########################
# EventBridge Schedule -> Run ECS Fargate Task
########################

resource "aws_cloudwatch_event_rule" "daily" {
  name                = "${local.short}-daily"
  description         = "Daily Interesting Chess data refresh"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "ecs_target" {
  rule     = aws_cloudwatch_event_rule.daily.name
  arn      = aws_ecs_cluster.main.arn
  role_arn = aws_iam_role.events_to_ecs.arn

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.chess_scraper.arn
    launch_type         = "FARGATE"
    platform_version    = "LATEST"
    
    network_configuration {
      subnets          = data.aws_subnets.default.ids
      security_groups  = [aws_security_group.ecs_tasks.id]
      assign_public_ip = true  # Needed for Fargate to download container images
    }
  }
}
