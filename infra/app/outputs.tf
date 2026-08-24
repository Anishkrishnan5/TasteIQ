output "application_url" {
  value       = "https://${aws_cloudfront_distribution.app.domain_name}"
  description = "Public TasteIQ URL. The same origin proxies API requests through CloudFront."
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.app.id
  description = "Used by the deployment workflow for frontend cache invalidations."
}

output "web_bucket_name" {
  value       = aws_s3_bucket.web.id
  description = "Static frontend deployment destination."
}

output "artifact_bucket_name" {
  value       = aws_s3_bucket.artifacts.id
  description = "Versioned retrieval and evaluation artifact storage."
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.api.name
}

output "ecs_task_definition_family" {
  value = aws_ecs_task_definition.api.family
}
