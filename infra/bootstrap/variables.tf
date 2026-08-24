variable "aws_region" {
  description = "AWS region for TasteIQ resources."
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Lowercase resource-name prefix."
  type        = string
  default     = "tasteiq"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project_name))
    error_message = "project_name must be 3-21 lowercase letters, digits, or hyphens."
  }
}

variable "github_repository" {
  description = "GitHub repository in owner/name form allowed to deploy from the production environment."
  type        = string

  validation {
    condition     = can(regex("^[^/]+/[^/]+$", var.github_repository))
    error_message = "github_repository must use owner/name form."
  }
}

variable "budget_alert_email" {
  description = "Email address for AWS budget alerts."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.budget_alert_email))
    error_message = "budget_alert_email must be a valid email address."
  }
}

variable "monthly_budget_usd" {
  description = "Monthly AWS cost budget in USD."
  type        = number
  default     = 35

  validation {
    condition     = var.monthly_budget_usd >= 5
    error_message = "monthly_budget_usd must be at least 5."
  }
}
