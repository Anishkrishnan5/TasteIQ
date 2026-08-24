variable "aws_region" {
  description = "AWS region for regional application resources."
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Lowercase resource-name prefix."
  type        = string
  default     = "tasteiq"
}

variable "api_image_uri" {
  description = "ECR image URI for the initial API task definition. Use a Git SHA tag or digest."
  type        = string

  validation {
    condition     = can(regex("[.:@][A-Za-z0-9_+.-]{7,}$", var.api_image_uri))
    error_message = "api_image_uri must include an immutable Git SHA tag or image digest."
  }
}

variable "desired_count" {
  description = "Steady-state ECS task count. One task is appropriate for the portfolio deployment."
  type        = number
  default     = 1

  validation {
    condition     = var.desired_count >= 1 && var.desired_count <= 2
    error_message = "desired_count must be between 1 and 2."
  }
}

variable "alarm_email" {
  description = "Optional email for CloudWatch alarm notifications. Confirmation is required."
  type        = string
  default     = ""

  validation {
    condition     = var.alarm_email == "" || can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alarm_email))
    error_message = "alarm_email must be empty or a valid email address."
  }
}
