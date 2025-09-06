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
  default_root_object = "index.html"

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
