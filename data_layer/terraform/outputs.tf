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

output "batch_job_queue_arn" {
  value = aws_batch_job_queue.queue.arn
}

output "batch_job_definition_arn" {
  value = aws_batch_job_definition.job.arn
}

output "aws_access_key_id" {
  value     = aws_iam_access_key.batch_user_key.id
  sensitive = false
  description = "AWS Access Key ID for boto3 authentication"
}

output "aws_secret_access_key" {
  value     = aws_iam_access_key.batch_user_key.secret
  sensitive = true
  description = "AWS Secret Access Key for boto3 authentication"
}

output "aws_region" {
  value = var.aws_region
  description = "AWS region for boto3 configuration"
}
