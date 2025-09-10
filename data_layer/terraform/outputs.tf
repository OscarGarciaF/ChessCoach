########################
# Outputs
########################

output "s3_bucket_name" {
  value = aws_s3_bucket.data.bucket
}

output "cloudfront_domain" {
  value       = var.create_cloudfront ? aws_cloudfront_distribution.cdn[0].domain_name : ""
  description = "If enabled, fetch https://<domain>/<latest_prefix>/results.json"
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_task_definition_arn" {
  value = aws_ecs_task_definition.chess_scraper.arn
}

output "ecs_autoscaling_group_name" {
  value       = aws_autoscaling_group.ecs.name
  description = "Auto Scaling Group name for ECS EC2 instances"
}

output "aws_region" {
  value       = var.aws_region
  description = "AWS region for ECS and S3 configuration"
}
