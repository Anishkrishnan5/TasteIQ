# TasteIQ AWS Infrastructure

TasteIQ uses two deliberately small Terraform stacks. `bootstrap` creates account-level delivery
primitives; `app` creates the application runtime. The split lets GitHub Actions publish an API image
before the first ECS service is created, without granting CI infrastructure-administrator access.

## Architecture

```text
GitHub Actions --OIDC--> ECR --immutable digest--> ECS Fargate
       |                                             |
       +--> S3 web bucket --> CloudFront --------> ALB
                                  |                  |
                                  +---- /api/* ------+

CloudWatch <-- logs, ALB metrics, ECS metrics
S3 artifacts <-- versioned offline retrieval artifacts
```

The VPC has two public subnets and no NAT gateway. Fargate tasks receive public IPs for outbound
dependency access, but their security group accepts inbound traffic only from the ALB. The ALB accepts
traffic only from AWS's CloudFront origin-facing managed prefix list. Users access one HTTPS CloudFront
origin, avoiding CORS and mixed-content problems without requiring a custom domain for v1.

## Prerequisites

- Terraform 1.15.x
- An AWS account with credentials authorized to create the declared resources
- A GitHub repository with a protected `production` environment
- Docker for publishing the initial API image

## 1. Bootstrap the account

```bash
cd infra/bootstrap
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out bootstrap.tfplan
terraform apply bootstrap.tfplan
```

The budget subscriber must confirm the AWS email. If the account already has the GitHub Actions OIDC
provider, import it before applying:

```bash
terraform import aws_iam_openid_connect_provider.github \
  arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com
```

Keep the one-time bootstrap state secure. The stack creates a private, encrypted, versioned S3 state
bucket for the application stack.

## 2. Publish the initial API image

Use the `api_repository_url` output and an immutable Git revision:

```bash
repository_url=$(terraform output -raw api_repository_url)
revision=$(git -C ../.. rev-parse HEAD)
aws ecr get-login-password --region us-west-2 \
  | docker login --username AWS --password-stdin "${repository_url%%/*}"
docker build -t "$repository_url:$revision" ../../backend
docker push "$repository_url:$revision"
```

## 3. Create the application stack

```bash
cd ../app
cp terraform.tfvars.example terraform.tfvars
terraform init \
  -backend-config="bucket=<terraform_state_bucket output>" \
  -backend-config="key=tasteiq/app.tfstate" \
  -backend-config="region=us-west-2"
terraform plan -out app.tfplan
terraform apply app.tfplan
```

The first CloudFront deployment can take several minutes. Confirm any SNS alarm subscription email.

## 4. Configure GitHub deployment variables

Set these repository or `production` environment variables from Terraform outputs:

| Variable | Source |
|---|---|
| `AWS_DEPLOY_ENABLED` | Set to `true` only after the first application apply |
| `AWS_REGION` | Terraform input, normally `us-west-2` |
| `AWS_ROLE_ARN` | Bootstrap `github_deploy_role_arn` |
| `ECR_REPOSITORY` | `tasteiq-api` unless the project name changed |
| `ECS_CLUSTER` | App `ecs_cluster_name` |
| `ECS_SERVICE` | App `ecs_service_name` |
| `ECS_TASK_FAMILY` | App `ecs_task_definition_family` |
| `WEB_BUCKET` | App `web_bucket_name` |
| `CLOUDFRONT_DISTRIBUTION_ID` | App `cloudfront_distribution_id` |
| `APP_URL` | App `application_url` |

The deploy role trusts only the repository's protected `production` environment and receives
short-lived OIDC credentials. It can publish the named application artifacts and deploy ECS task
revisions; it cannot apply Terraform infrastructure.

## Deployment and rollback

Pushes to `main` deploy only after `AWS_DEPLOY_ENABLED=true`. Manual workflow dispatch accepts a prior
Git commit or release tag. Every API task uses an ECR digest resolved from an immutable Git-SHA tag.

To roll back, dispatch `Deploy AWS` with the last known-good Git revision. Existing ECR images are
reused rather than overwritten, a new ECS task revision points to the prior digest, and the frontend is
rebuilt from the same revision. ECS waits for service stability before frontend publication. GitHub's
deployment summary records the image digest and task-definition ARN.

Retrieval artifacts belong in the versioned artifact bucket. Restore a prior S3 object version and
redeploy the matching application revision if an artifact rollback is required.

## Cost controls

The bootstrap stack creates forecasted and actual monthly budget notifications. The application uses
one small Fargate task, two public subnets, no NAT gateway, CloudFront's lowest price class, short log
retention, and a maximum of two autoscaled tasks. The ALB and continuously running Fargate task are the
main fixed costs. Run `terraform destroy` in `infra/app` when the public demo is no longer needed.

The protected state and ECR repository are intentionally not force-deleted.

## Validation

```bash
make infra-check
```

This formats, initializes without the remote backend, and provider-validates both stacks. Validation
does not contact an AWS account or prove that an apply will be authorized; review a real `terraform
plan` before deployment.
