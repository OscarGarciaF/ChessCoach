########################
# Variables
########################

variable "project_name" {
  type    = string
  default = "interesting-chess"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# Data/config passed to the container/script
variable "app_name" {
  type    = string
  default = "interesting-chess"
}

variable "app_version" {
  type    = string
  default = "1.0.0"
}

variable "username" {
  type    = string
  default = "alienoscar"
}

variable "email" {
  type    = string
  default = "garcia.oscar1729@gmail.com"
}

variable "titles" {
  type    = string
  default = "GM,WGM,IM,WIM,FM,WFM,NM,WNM,CM,WCM"
}

variable "days_window" {
  type    = number
  default = 30
}

variable "request_sleep_s" {
  type    = number
  default = 0.25
}

variable "limit_players" {
  type    = number
  default = 0
}   # 0 = no limit

# Schedule: cron(5 3 * * ? *) == 03:05 UTC daily
variable "schedule_expression" {
  type    = string
  default = "cron(5 3 * * ? *)"
}

# Optional CloudFront
variable "create_cloudfront" {
  type    = bool
  default = true
}

# Path to your python scraping directory on local disk
variable "scraping_dir_path" {
  type    = string
  default = null
  # Provide a value to override; if null/empty, we fallback to ${path.module}/../scraping in locals
}
