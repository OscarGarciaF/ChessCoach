locals {
  short         = lower(replace(replace(replace(var.project_name, " ", "-"), "_", "-"), ".", "-"))
  suffix        = random_id.sfx.hex
  bucket_name   = "${local.short}-data-${local.suffix}"
  latest_prefix = "data"
  code_prefix   = "code"
  code_bucket_name = "${local.short}-code-${local.suffix}"
  scraping_dir_path_effective = var.scraping_dir_path != null && var.scraping_dir_path != "" ? var.scraping_dir_path : "${path.module}/../scraping"
}

resource "random_id" "sfx" { byte_length = 3 }
