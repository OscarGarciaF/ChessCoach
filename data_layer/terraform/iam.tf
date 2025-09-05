########################
# IAM
########################

# Batch service role
data "aws_iam_policy" "batch_service_managed" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

resource "aws_iam_role" "batch_service" {
  name               = "${local.short}-batch-svc-${local.suffix}"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{ Effect="Allow", Principal={ Service="batch.amazonaws.com" }, Action="sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy_attachment" "batch_service_attach" {
  role       = aws_iam_role.batch_service.name
  policy_arn = data.aws_iam_policy.batch_service_managed.arn
}

# ECS instance role/profile for Batch EC2
data "aws_iam_policy" "ecs_instance_managed" {
  arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}
data "aws_iam_policy" "ecr_readonly" {
  arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}
resource "aws_iam_role" "ecs_instance" {
  name               = "${local.short}-ecs-inst-${local.suffix}"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{ Effect="Allow", Principal={ Service="ec2.amazonaws.com" }, Action="sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy_attachment" "ecs_inst_attach1" {
  role       = aws_iam_role.ecs_instance.name
  policy_arn = data.aws_iam_policy.ecs_instance_managed.arn
}
resource "aws_iam_role_policy_attachment" "ecs_inst_attach2" {
  role       = aws_iam_role.ecs_instance.name
  policy_arn = data.aws_iam_policy.ecr_readonly.arn
}
resource "aws_iam_instance_profile" "ecs_instance_profile" {
  name = "${local.short}-ecs-prof-${local.suffix}"
  role = aws_iam_role.ecs_instance.name
}

# Job role (permissions used by the container to read code & write outputs)
resource "aws_iam_role" "job_role" {
  name               = "${local.short}-job-role-${local.suffix}"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{ Effect="Allow", Principal={ Service="ecs-tasks.amazonaws.com" }, Action="sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy" "job_role_policy" {
  role = aws_iam_role.job_role.id
  policy = jsonencode({
    Version="2012-10-17",
    Statement=[
      {
        Sid="ReadCode", Effect="Allow",
        Action=["s3:GetObject"],
        Resource="${aws_s3_bucket.data.arn}/${local.code_prefix}/*"
      },
      {
        Sid="WriteOutputs", Effect="Allow",
        Action=["s3:PutObject","s3:PutObjectAcl"],
        Resource="${aws_s3_bucket.data.arn}/${local.latest_prefix}/*"
      },
      {
        Sid="ListBucket", Effect="Allow",
        Action=["s3:ListBucket"],
        Resource=aws_s3_bucket.data.arn
      }
    ]
  })
}

# EventBridge -> Batch submit role
resource "aws_iam_role" "events_to_batch" {
  name               = "${local.short}-events-${local.suffix}"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{ Effect="Allow", Principal={ Service="events.amazonaws.com" }, Action="sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy" "events_to_batch_policy" {
  role = aws_iam_role.events_to_batch.id
  policy = jsonencode({
    Version="2012-10-17",
    Statement=[{
      Effect="Allow",
      Action=["batch:SubmitJob"],
      Resource=[aws_batch_job_queue.queue.arn, aws_batch_job_definition.job.arn]
    }]
  })
}

########################
# IAM User for Programmatic Access (for boto3)
########################

resource "aws_iam_user" "batch_user" {
  name = "${local.short}-batch-user-${local.suffix}"
  path = "/"
}

resource "aws_iam_access_key" "batch_user_key" {
  user = aws_iam_user.batch_user.name
}

resource "aws_iam_user_policy" "batch_user_policy" {
  name = "${local.short}-batch-user-policy"
  user = aws_iam_user.batch_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*"
        ]
      }
    ]
  })
}
