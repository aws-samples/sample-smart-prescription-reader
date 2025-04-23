# Security

## Health Related Data

Since you might use this AWS Content to work with health-related data, you should perform your own independent
assessment, and take measures to ensure that you comply with the local rules, laws, regulations, terms of use that apply
to you and your content, and to ensure that you comply with your own specific quality control practices and standards.

## Amazon Bedrock

Given the use case, there is a risk that the models may produce medical advice. We assume that coercing the output to
json with a structured schema should be enough mitigation to avoid having the model providing medical advice. Explicit
guardrails should be included.

## Shared Responsibility Model

Security and Compliance is a shared responsibility between AWS and the customer.
This shared model can help relieve the customer’s operational burden as AWS operates, manages and controls the
components from the host operating system and virtualization layer down to the physical security of the facilities in
which the service operates.
The customer assumes responsibility and management of the guest operating system (including updates and security
patches), other associated application software as well as the configuration of the AWS provided security group
firewall. Customers should carefully consider the services they choose as their responsibilities vary depending on the
services used, the integration of those services into their IT environment, and applicable laws and regulations. The
nature of this shared responsibility also provides the flexibility and customer control that permits the deployment. As
shown in the chart below, this differentiation of responsibility is commonly referred to as Security “of” the Cloud
versus Security “in” the Cloud.
For more details, please refer
to [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/).

## IAM Governance

AWS has a series
of [best practices and guidelines](https://docs.aws.amazon.com/IAM/latest/UserGuide/IAMBestPracticesAndUseCases.html)
around IAM.

### AWS Managed Policies

In this prototype, we used the default AWSLambdaBasicExecutionRole AWS Managed Policy to facilitate development. AWS
Managed Policies don’t grant least privileges in order to cover common use cases. The best practice it to write a custom
policy with only the permissions needed by the task.
More information: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-use-aws-defined-policies.

### Wildcard Policies

In this prototype, some policies use wildcards to specify resources to expedite development. The best practice is to
create policies that grant least privileges.
More information: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege

## S3

Amazon S3 provides a number of security features to consider as you develop and implement your own security policies.
The following best practices are general guidelines and don’t represent a complete security solution. Because these best
practices might not be appropriate or sufficient for your environment, treat them as helpful considerations rather than
prescriptions.

For an in-depth description of best practices around S3, please refer
to [Security Best Practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html).
At a minimum, we recommend that you:

1. Ensure that your Amazon S3 buckets use the correct policies and are not publicly accessible;
2. Implement least privilege access;
3. Consider encryption at-rest (on disk);
4. Enforce encryption in-transit by restricting access using secure transport (TLS);
5. Enable object versioning when applicable; and
6. Enable cross-region replication as a disaster recovery strategy;
7. Consider if the data stored in the buckets warrants enabling MFA delete.

## DynamoDB

We implement encryption at rest with AWS KMS Customer Managed Keys. You may want to consider implementing client-side
encryption to further protect sensitive data.

For an in-depth description of best practices around DynamoDB, please refer
to [DynamoDB security best practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices-security.html).

## CDK/CloudFormation

You can prevent stacks from being accidentally deleted by enabling termination protection on the stack. If a user
attempts to delete a stack with termination protection enabled, the deletion fails and the stack, including its status,
remains unchanged. For more details on how to enable the deletion protection, refer to [
`termination_protection` configuration](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib-readme.html#termination-protection).

## VPC

In this prototype, a VPC is configured with isolated subnets and interface endpoints.

* All Lambda functions run in isolated subnets with no internet access
* Interface endpoints provide private connectivity to AWS services:
    - Amazon Bedrock for AI model inference
    - Systems Manager for configuration parameters
* Gateway endpoints for private connectivity to Amazon S3 and AWS DynamoDB.

For an in-depth description of best practices around VPC, please refer
to [Security Best Practices for Amazon VPC](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html).

## Logs

Logging can become verbose in prod and too many logs can make analysis difficult. Logging can also disclose data. For
further AWS-recommended best practices,
see [Logging best practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/logging-monitoring-for-application-owners/logging-best-practices.html).

## KMS

This prototype using KMS Customer Managed Keys(CMK). The default key policies permit any principal in the account to use
the keys. Consider creating key policies that implement separation of duties so that key administrators can't encrypt or
decrypt with the keys. For troubleshooting, you could create a break glass role with decryption access and log and alert
on any
usage.

KMS generates EventBridge events, it is recommended to route these events to target functions so they can be monitored
properly. KMS also reports to Security Hub, and it can be beneficial to monitor the KMS state and its compliance with
various security frameworks. 
