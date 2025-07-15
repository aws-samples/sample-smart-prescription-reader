# Project Structure

## Monorepo Organization

This is an Nx monorepo with packages organized by domain and function:

```
├── packages/
│   ├── core/                    # Python business logic (Lambda functions)
│   ├── infra/                   # AWS CDK infrastructure code
│   ├── demo/                    # React demo application
│   └── common/                  # Shared libraries
│       ├── constructs/          # Reusable CDK constructs
│       ├── models-graphql/      # GraphQL schema and generated types
│       └── types/               # Shared TypeScript types
├── documentation/               # Architecture and technical docs
├── notebooks/                   # Jupyter notebooks for data analysis
└── scripts/                     # Build and utility scripts
```

## Package Details

### packages/core/ (Python)
```
smart_prescription_reader/
├── lambda_handlers/             # AWS Lambda entry points
│   ├── extract_prescription.py # Initial data extraction handler
│   ├── evaluate_response.py    # Quality evaluation handler
│   ├── correct_response.py     # Data correction handler
│   ├── ocr.py                  # Textract OCR handler
│   ├── process_prescription.py # Main workflow trigger
│   ├── update_job_status.py    # Job status updates
│   └── upload_file.py          # S3 presigned URL generation
├── PrescriptionProcessor/       # Core AI processing logic
│   ├── processor.py            # Base processor with Bedrock integration
│   ├── extract.py              # Extraction logic and prompts
│   ├── evaluate.py             # Quality evaluation logic
│   ├── correct.py              # Correction logic
│   ├── config.py               # Configuration management
│   └── utils.py                # Image handling and S3 utilities
├── JobStatus/                   # Job state management
│   ├── base.py                 # Abstract repository interface
│   ├── dynamodb.py             # DynamoDB implementation
│   └── local.py                # Local/testing implementation
├── models/                      # Pydantic data models
│   ├── schema.py               # GraphQL-generated models
│   └── workflow.py             # Step Functions workflow models
├── prompts/                     # Jinja2 templates for AI prompts
│   ├── extract_prescription.jinja2
│   ├── evaluate_extraction.jinja2
│   └── corrections.jinja2
└── utils/                       # Shared utilities
    ├── bedrock_runtime_client.py # Bedrock API wrapper with retry logic
    ├── ocr_service.py           # Textract service wrapper
    ├── textract_helper.py       # Text extraction utilities
    └── exceptions.py            # Custom exception classes
```

### packages/infra/ (TypeScript CDK)
```
src/
├── constructs/                  # Reusable CDK constructs
│   ├── api/                     # AppSync GraphQL API constructs
│   │   ├── appSyncDataSources.ts # Data source configurations
│   │   ├── graphqlApi.ts        # GraphQL API definition
│   │   └── resolvers/           # JavaScript resolvers
│   ├── website/                 # Static website hosting
│   │   └── demoWebsite.ts       # S3/CloudFront website construct
│   ├── workflow/                # Step Functions workflow
│   │   ├── smartPrescriptionReaderWorkflow.ts # Main workflow
│   │   └── taskFunctions/       # Lambda function constructs
│   │       ├── extractPrescription.ts
│   │       ├── evaluateResponse.ts
│   │       ├── correctResponse.ts
│   │       ├── ocrPrescription.ts
│   │       └── updateJobStatus.ts
│   ├── bedrockPolicy.ts         # IAM policies for Bedrock access
│   ├── secureBucket.ts          # S3 bucket with security defaults
│   └── smartPrescriptionReaderCode.ts # Code bundling utilities
├── stacks/
│   └── applicationStack.ts      # Main CDK stack definition
└── main.ts                      # CDK app entry point with PDK/Nag
```

### packages/demo/ (React)
```
src/
├── components/                  # React components
│   ├── AppLayout/               # Main application layout
│   ├── CognitoAuth/             # Authentication components
│   ├── DisplayPrescription.tsx  # Results display
│   ├── GenerationOptions/       # Model configuration forms
│   ├── ImageUploader.tsx        # File upload component
│   ├── NewPrescriptionForm.tsx  # Main form component
│   ├── PrescriptionForm.tsx     # Form wrapper
│   ├── RuntimeConfig/           # Configuration management
│   ├── SchemaSelector/          # JSON schema selection
│   ├── StateProgress.tsx        # Processing status display
│   └── resizeImages.ts          # Image processing utilities
├── hooks/                       # Custom React hooks
│   ├── useAppLayout.tsx         # Layout state management
│   ├── useGlobalUIContext.ts    # Global UI state
│   ├── useGraphqlClient.ts      # GraphQL client setup
│   ├── usePrescriptionExtraction.ts # Main extraction logic
│   └── useRuntimeConfig.tsx     # Configuration loading
├── pages/
│   └── SmartPrescriptionReader.tsx # Main page component
├── routes/                      # TanStack Router routes
│   ├── __root.tsx               # Root route layout
│   ├── index.tsx                # Home route
│   └── smartPrescriptionReader/index.tsx # Main app route
└── config.ts                    # App configuration
```

### packages/common/models-graphql/
```
src/
├── schema/                      # GraphQL schema definitions
├── documents/                   # GraphQL queries/mutations
└── graphql/                     # Generated TypeScript types
```

## Naming Conventions

### Files and Directories
- **kebab-case**: Package names, file names, directories
- **PascalCase**: React components, CDK constructs, Python classes
- **camelCase**: TypeScript functions, variables, GraphQL fields
- **snake_case**: Python functions, variables, file names

### Packages
- Scoped with `@smart-prescription-reader/` prefix
- Use descriptive names: `core`, `infra`, `demo`, `common-constructs`

### CDK Resources
- Use descriptive construct names with context
- Follow AWS resource naming conventions
- Apply consistent tagging strategy

### Lambda Functions
- Handler files named by function: `extract_prescription.py`
- Use descriptive function names in Step Functions
- Follow AWS Lambda Powertools patterns

## Configuration Management

### Environment-Specific Config
- **CDK Context**: `cdk.context.json` for CDK-specific settings
- **Runtime Config**: S3-hosted JSON for frontend configuration
- **Parameter Store**: Lambda function configuration
- **Environment Variables**: Service-specific settings

### Shared Configuration
- **GraphQL Schema**: Single source of truth in `models-graphql`
- **Type Generation**: Automated from GraphQL schema
- **CDK Constructs**: Reusable infrastructure patterns

## Development Patterns

### Code Organization
- **Separation of Concerns**: Clear boundaries between packages
- **Shared Libraries**: Common functionality in `packages/common/`
- **Type Safety**: Generated types from GraphQL schema
- **Infrastructure as Code**: All AWS resources defined in CDK

### Python Patterns (packages/core/)
- **Repository Pattern**: Abstract base classes with DynamoDB/local implementations
- **Dependency Injection**: Services injected into Lambda handlers
- **Error Handling**: Custom exceptions with retry logic using Tenacity
- **Configuration**: Pydantic models with SSM Parameter Store integration
- **Prompt Engineering**: Jinja2 templates for consistent AI prompts
- **Response Parsing**: Structured extraction using regex and JSON repair

### CDK Patterns (packages/infra/)
- **Construct Composition**: Reusable constructs for common patterns
- **Security by Default**: SecureBucket, VPC isolation, KMS encryption
- **Policy Management**: Centralized IAM policies for Bedrock access
- **Environment Separation**: Context-driven configuration
- **Compliance**: CDK Nag integration for security rule checking

### React Patterns (packages/demo/)
- **Custom Hooks**: Business logic separated from UI components
- **Context Providers**: Global state management for UI and auth
- **Type-Safe Routing**: TanStack Router with generated route types
- **GraphQL Integration**: TanStack Query for data fetching
- **Component Composition**: Cloudscape Design System components

### Testing Strategy
- **Unit Tests**: Each package has its own test suite using MagicMock for mocking
- **Integration Tests**: End-to-end testing with real AWS services (marked with `@pytest.mark.integration`)
- **No External Mocking**: Unit tests use MagicMock, integration tests use real AWS services
- **Test Fixtures**: Shared test data and mock configurations

### Build and Deploy
- **Nx Targets**: Consistent build, test, lint, deploy commands
- **Dependency Management**: Nx handles inter-package dependencies
- **Parallel Execution**: Nx optimizes build and test execution
- **Code Generation**: GraphQL schema generates TypeScript types automatically