# Technology Stack

## Build System & Monorepo Management

- **Nx**: Monorepo build system and task orchestration
- **pnpm**: TypeScript package manager with workspace support
- **uv**: Python package and project manager for all Python dependencies
- **TypeScript**: Primary language for infrastructure and frontend
- **Python 3.13+**: Backend business logic and Lambda functions

## Core Technologies

### Infrastructure (CDK)

- **AWS CDK v2**: Infrastructure as Code
- **CDK Nag**: Security and compliance rule checking
- **PDK (Project Development Kit)**: AWS best practices and constructs

### Backend (Python)

- **AWS Lambda Powertools**: Logging, tracing, metrics, and event parsing
- **Pydantic v2**: Data validation and serialization with GraphQL schema generation
- **Boto3**: AWS SDK for Python with type stubs for better IDE support
- **Jinja2**: Template engine for AI prompts (extract, evaluate, correct)
- **Tenacity**: Retry logic for Bedrock API calls with exponential backoff
- **JSON Repair**: Handles malformed JSON responses from AI models
- **pytest**: Testing framework for unit and integration tests
- **Ruff**: Fast Python linter and formatter replacing flake8/black

### Frontend (React)

- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **TanStack Router**: Type-safe routing
- **Cloudscape Design System**: AWS-native UI components
- **TanStack Query**: Data fetching and caching

### AWS Services

- **Amazon Bedrock**: AI/ML foundation models (Claude, Nova models)
- **AWS Step Functions**: Workflow orchestration with error handling
- **AWS AppSync**: GraphQL API with real-time subscriptions
- **Amazon DynamoDB**: Job status storage with TTL
- **Amazon S3**: Image and configuration storage with presigned URLs
- **Amazon Textract**: OCR service for text extraction
- **Amazon Cognito**: User authentication and authorization
- **AWS Systems Manager**: Parameter Store for Lambda configuration
- **AWS KMS**: Customer-managed keys for encryption
- **Amazon VPC**: Network isolation with interface endpoints

## AI/ML Configuration Patterns

### Model Selection Strategy

- **Fast Model**: Quick initial extraction (e.g., Claude 3 Haiku)
- **Judge Model**: Quality evaluation (e.g., Claude 4 Sonnet)
- **Powerful Model**: Complex corrections (e.g., Claude 4 Sonnet)

### Prompt Engineering

- **Jinja2 Templates**: Consistent prompt structure across models
- **System Prompts**: Role definition and output format specification
- **Few-shot Examples**: Embedded examples for better extraction
- **Chain of Thought**: Thinking tags for model reasoning
- **Response Prefilling**: Structured JSON output formatting

### Cost Optimization

- **Prompt Caching**: Cache frequently used instructions
- **Progressive Processing**: Use expensive models only when needed
- **Configurable Iterations**: Limit correction attempts
- **Model-specific Features**: Leverage prompt caching for supported models

### Configuration Management

```json
{
  "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
  "temperature": 0.0,
  "medicationsKey": "medications/drug-list.txt",
  "glossaryKey": "glossary/prescription-terms.txt",
  "thinking": true,
  "transcribe": false,
  "promptCacheModels": ["anthropic.claude-3-7-sonnet-20250219-v1:0"]
}
```

## Common Commands

### Setup

```bash
# Install dependencies
pnpm install

# Install global tools
npm install -g aws-cdk
cdk bootstrap
```

### Development

```bash
# Build all packages
nx --outputStyle=static run-many --target=build --parallel

# Run tests
nx --outputStyle=static run-many --target=test --parallel

# Lint code
nx --outputStyle=static run-many --target=lint --parallel

# Generate GraphQL types
nx --outputStyle=static run-many --target=generate --parallel
```

### Infrastructure

```bash
# Deploy infrastructure (pipe through tail to manage output)
nx --outputStyle=static deploy @smart-prescription-reader/infra | tail -n 100

# Deploy with hotswap (dev only)
nx --outputStyle=static deploy @smart-prescription-reader/infra --hotswap | tail -n 100

# Run CDK diff
nx --outputStyle=static run @smart-prescription-reader/infra:diff
```

### Frontend Development

```bash
# Start demo app
nx --outputStyle=static serve @smart-prescription-reader/demo

# Build demo app
nx --outputStyle=static build @smart-prescription-reader/demo
```

### Python Development

```bash
# Install Python dependencies (in packages/core)
uv sync

# Run Python tests
uv run pytest

# Run integration tests
uv run pytest -m integration

# Format Python code
uv run ruff format

# Lint Python code
uv run ruff check
```

> **Important**: All unit and integration tests must pass before completing any Python changes. This ensures code quality and prevents regressions.

## Code Quality Tools

- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting
- **Ruff**: Python linting and formatting
- **Vitest**: JavaScript/TypeScript testing
- **pytest**: Python testing
