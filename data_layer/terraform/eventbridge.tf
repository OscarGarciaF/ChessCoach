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
