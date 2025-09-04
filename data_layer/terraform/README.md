# Terraform Infrastructure for Interesting Chess

This Terraform configuration deploys the infrastructure needed to run the Interesting Chess data scraper on AWS using AWS Batch.

## Architecture

The infrastructure includes:
- **S3 Bucket**: Stores the Python code and output data
- **CloudFront Distribution** (optional): CDN for serving the results
- **AWS Batch**: Managed compute environment for running the scraper
- **EventBridge**: Scheduled trigger for daily execution
- **IAM Roles**: Proper permissions for all components

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (>= 1.5.0)
3. Python scraping code in `../scraping/` directory

## Quick Start

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your configuration:
   - Set your Chess.com username and email
   - Adjust the AWS region if needed
   - Configure scraping parameters

3. Initialize and apply Terraform:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Name of the project | `"interesting-chess"` |
| `aws_region` | AWS region for deployment | `"us-east-1"` |
| `app_name` | Application name for User-Agent | `"interesting-chess"` |
| `version` | Application version | `"1.0.0"` |
| `username` | Your Chess.com username | Required |
| `email` | Your contact email | Required |
| `titles` | Chess titles to scrape | All standard titles |
| `days_window` | Days to look back for games | `30` |
| `request_sleep_s` | Sleep between API requests | `0.25` |
| `limit_players` | Limit players for testing | `0` (no limit) |
| `schedule_expression` | Cron expression for scheduling | Daily at 03:05 UTC |
| `create_cloudfront` | Enable CloudFront distribution | `true` |

## Outputs

After successful deployment, Terraform will output:

- `s3_bucket_name`: S3 bucket where data is stored
- `cloudfront_domain`: CloudFront domain (if enabled)
- `aws_access_key_id`: AWS access key for boto3
- `aws_secret_access_key`: AWS secret key for boto3 (sensitive)
- `aws_region`: AWS region for boto3 configuration

## File Structure

The scraper expects this file structure:
```
../scraping/
├── main.py              # Main application entry point
├── chess_api.py         # Chess.com API client
├── config.py           # Configuration constants
├── models.py           # Data models
├── probability.py      # Statistical calculations
├── streak_analyzer.py  # Streak analysis logic
├── requirements.txt    # Python dependencies
└── data/              # Output directory (created at runtime)
```

## Data Access

The scraper outputs results to S3 in JSON format:
- Direct S3 access: `s3://{bucket}/latest/results.json`
- CloudFront access: `https://{cloudfront_domain}/latest/results.json`

## Security

- IAM roles follow the principle of least privilege
- S3 bucket has public access blocked by default
- CloudFront uses Origin Access Control (OAC) for secure S3 access
- Separate IAM user created for programmatic access with limited permissions

## Monitoring

- AWS Batch provides job execution logs in CloudWatch
- EventBridge rules can be monitored for execution status
- S3 objects include metadata for debugging

## Cost Optimization

- Uses t2.micro and t3.micro instances (Free Tier eligible)
- Batch compute environment scales to zero when not running
- CloudFront caching reduces S3 requests
- Lifecycle policies can be added for log retention

## Troubleshooting

1. **Job fails to start**: Check IAM permissions and Batch compute environment status
2. **Code not found**: Ensure the scraping directory exists and files are uploaded
3. **S3 access denied**: Verify IAM roles and bucket policies
4. **CloudFront not serving**: Check OAC configuration and cache invalidation

For detailed logs, check AWS Batch job logs in CloudWatch.
