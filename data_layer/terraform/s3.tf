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

# Upload the Python scraping files for the Batch job to download
data "archive_file" "scraping_code" {
  type        = "zip"
  source_dir  = local.scraping_dir_path_effective
  output_path = "${path.module}/scraping.zip"
  excludes    = ["__pycache__", "*.pyc", "data", ".dockerignore"]
}

resource "aws_s3_object" "scraping_code" {
  bucket = aws_s3_bucket.data.id
  key    = "${local.code_prefix}/scraping.zip"
  source = data.archive_file.scraping_code.output_path
  etag   = filemd5(data.archive_file.scraping_code.output_path)
}
