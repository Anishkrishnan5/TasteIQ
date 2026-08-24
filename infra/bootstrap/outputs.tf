output "api_repository_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "ECR repository used by the API deployment workflow."
}

output "github_deploy_role_arn" {
  value       = aws_iam_role.github_deploy.arn
  description = "Set this as the GitHub Actions AWS_ROLE_ARN repository variable."
}

output "terraform_state_bucket" {
  value       = aws_s3_bucket.terraform_state.id
  description = "Use this bucket when initializing the application stack backend."
}
