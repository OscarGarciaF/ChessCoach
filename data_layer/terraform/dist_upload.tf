########################
# Upload static `dist` folder to S3 (non-destructive sync)
# This will create individual aws_s3_object resources for each file under the
# local `dist` directory and place them at the root of the bucket. It does NOT
# delete or manage objects already present in the bucket.
########################

locals {
  # path to the dist to upload; assumed to be at repo root ./dist
  # from this module (data_layer/terraform) go up two levels to repo root then /dist
  dist_dir = "${path.module}/../../dist/public"
  # if dist_dir exists, gather files recursively; otherwise use empty list to avoid errors
  # `fileexists()` errors for directories, so use `can(fileset(...))` which succeeds
  # only when the directory exists and fileset can read it.
  dist_files = can(fileset(local.dist_dir, "**/*")) ? fileset(local.dist_dir, "**/*") : []
  dist_dir_exists = can(fileset(local.dist_dir, "**/*"))
}

resource "aws_s3_object" "dist_files" {
  for_each = { for f in local.dist_files : f => f }

  bucket = aws_s3_bucket.data.id

  # Put files at the bucket root preserving relative path from dist
  key    = each.key

  source = "${local.dist_dir}/${each.value}"

  # Use etag to force updates when file changes
  etag = filemd5("${local.dist_dir}/${each.value}")

  # Ensure objects inherit bucket-level settings; set ACL to private
  acl = "private"

  # Set content type if possible, fall back to binary/octet-stream
  content_type = lookup(
    {
      "html" = "text/html",
      "css"  = "text/css",
      "js"   = "application/javascript",
      "json" = "application/json",
      "svg"  = "image/svg+xml",
      "png"  = "image/png",
      "jpg"  = "image/jpeg",
      "jpeg" = "image/jpeg",
      "txt"  = "text/plain",
    },
    # compute file extension by splitting the basename on '.' and taking last element
    lower(
      element(
        split(".", basename(each.key)),
        length(split(".", basename(each.key))) - 1
      )
    ),
    "binary/octet-stream"
  )
}

output "dist_upload_count" {
  value = length(local.dist_files)
  description = "Number of files in local dist directory that will be uploaded to S3 as individual objects."
}

output "dist_dir_path" {
  value       = local.dist_dir
  description = "Local path used for the dist directory (for debugging)."
}

output "dist_dir_exists" {
  value       = local.dist_dir_exists
  description = "True if the dist directory exists on the machine where Terraform is run."
}
