# Terraform Infrastructure for Interesting Chess

This Terraform configuration deploys the infrastructure needed to run the Interesting Chess data scraper on AWS using ECS

## Architecture

The infrastructure includes:
- **S3 Buckets**: Separate buckets for Python code and output data
- **CloudFront Distribution** (optional): CDN for serving the results with custom domain support
- **ECS Cluster**: Managed compute environment for running the scraper on EC2
- **Auto Scaling Group**: EC2 instances with spot pricing for cost optimization
- **EventBridge**: Scheduled trigger for daily execution
- **IAM Roles**: Proper permissions for all components
- **VPC & Security Groups**: Network isolation and security
- **CloudWatch Logs**: Centralized logging for debugging

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
| `app_version` | Application version | `"1.0.0"` |
| `username` | Your Chess.com username | `"alienoscar"` |
| `email` | Your contact email | `"garcia.oscar1729@gmail.com"` |
| `titles` | Chess titles to scrape | `"GM,WGM,IM,WIM,FM,WFM,NM,WNM,CM,WCM"` |
| `days_window` | Days to look back for games | `30` |
| `request_sleep_s` | Sleep between API requests | `0.25` |
| `limit_players` | Limit players for testing | `0` (no limit) |
| `schedule_expression` | Cron expression for scheduling | `"cron(5 3 * * ? *)"` (Daily at 03:05 UTC) |
| `create_cloudfront` | Enable CloudFront distribution | `true` |
| `scraping_dir_path` | Path to Python scraping directory | `null` (auto-detects ../scraping) |
| `acm_certificate_arn` | ARN of ACM certificate for custom domain | `null` (optional) |
| `alternate_domain_names` | Custom domain names for CloudFront | `["interestingchess.com", "www.interestingchess.com"]` |

## Outputs

After successful deployment, Terraform will output:

- `s3_bucket_name`: S3 bucket where data is stored
- `cloudfront_domain`: CloudFront domain (if enabled)
- `ecs_cluster_name`: ECS cluster name
- `ecs_task_definition_arn`: ECS task definition ARN
- `ecs_autoscaling_group_name`: Auto Scaling Group name for ECS EC2 instances
- `aws_region`: AWS region for configuration

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

The infrastructure also supports uploading static website files from a local `dist` directory to serve alongside the data.

## Security

- IAM roles follow the principle of least privilege
- S3 bucket has public access blocked by default
- CloudFront uses Origin Access Control (OAC) for secure S3 access
- Separate IAM user created for programmatic access with limited permissions

## Monitoring

- ECS tasks provide execution logs in CloudWatch
- Auto Scaling Group metrics available in CloudWatch
- EventBridge rules can be monitored for execution status
- S3 objects include metadata for debugging
- Container insights enabled for cluster-level monitoring

## Cost Optimization

- Uses EC2 spot instances (t3a.micro, t3.micro, t2.micro) with significant cost savings
- Auto Scaling Group scales to zero when not running (min: 0, max: 1)
- ECS cluster uses managed capacity providers for efficient resource allocation
- CloudFront caching reduces S3 requests
- Separate S3 buckets for code and data optimize access patterns
- 14-day CloudWatch log retention to control storage costs

## Troubleshooting

1. **Task fails to start**: Check IAM permissions, ECS cluster status, and Auto Scaling Group capacity
2. **No EC2 instances available**: Verify ASG desired capacity and check EC2 limits in your AWS account
3. **Code not found**: Ensure the scraping directory exists and code bucket upload succeeded
4. **S3 access denied**: Verify ECS task role permissions and bucket policies
5. **CloudFront not serving**: Check Origin Access Control (OAC) configuration and cache invalidation
6. **Container fails**: Check ECS task logs in CloudWatch for Python execution errors
7. **Spot instance interruptions**: Monitor ASG for instance replacements and scaling events

For detailed logs, check ECS task logs in CloudWatch under `/ecs/{project-name}-chess-scraper`.
