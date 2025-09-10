########################
# EventBridge Schedule -> Run ECS EC2 Task
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
    launch_type         = "EC2"
    platform_version    = "LATEST"
    task_count          = 1

    # No network_configuration needed for EC2 launch type with bridge networking
  }
}
