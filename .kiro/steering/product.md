# Smart Prescription Reader

The Smart Prescription Reader is a prototype solution that extracts structured data from prescription images using AWS Bedrock foundation models. It employs a multi-stage AI approach with specialized models for extraction, evaluation, and correction, ensuring high accuracy while optimizing for cost and performance.

## Key Features

- **Multi-stage AI Processing**: Uses different models for extraction (fast), evaluation (judge), and correction (powerful)
- **Adaptive Intelligence**: Balances speed, accuracy, and cost - simple prescriptions processed quickly, complex cases get additional attention
- **Quality Assurance**: Rates extraction quality from "Poor" to "Excellent" with automated correction triggers
- **Serverless Architecture**: Built on AWS Lambda, Step Functions, AppSync, and other serverless services
- **Security-First**: Handles sensitive medical information with VPC isolation, KMS encryption, and IAM controls
- **Cost Optimization**: Balances accuracy with cost through intelligent model selection and prompt caching
- **Real-time Processing**: GraphQL API with job status tracking for async processing

## Multi-Stage Workflow

1. **OCR Extraction**: Amazon Textract extracts raw text from prescription images
2. **Initial Extraction**: Fast Bedrock model quickly identifies key elements (patient details, medications, dosage)
3. **Quality Evaluation**: Separate evaluation model assesses extraction quality and provides feedback
4. **Intelligent Correction**: If needed, powerful model corrects data based on specific feedback
5. **Result Storage**: Final structured data stored with confidence scores and usage metrics

## Target Use Case

Automates document processing for healthcare organizations by converting prescription images into structured, machine-readable data while maintaining high accuracy through automated quality checks and corrections.

## Architecture Pattern

The solution follows a serverless event-driven architecture with:
- **API Layer**: AppSync GraphQL API with Cognito authentication
- **Orchestration**: Step Functions state machine coordinating multi-step workflow
- **Compute**: Lambda functions for each processing stage
- **AI/ML**: Textract for OCR, Bedrock for foundation model access
- **Storage**: S3 for images/config, DynamoDB for job status tracking
- **Security**: VPC isolation, KMS encryption, IAM policies