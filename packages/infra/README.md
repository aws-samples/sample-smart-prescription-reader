# @smart-prescription-reader/infra

This library was generated with [@aws/nx-plugin](https://github.com/awslabs/nx-plugin-for-aws/).

## Building

Run `pnpm exec nx build @smart-prescription-reader/infra [--skip-nx-cache]` to build the application.

## Running unit tests

Run `pnpm exec nx test @smart-prescription-reader/infra` to execute the unit tests via Vitest.

### Updating snapshots

To update snapshots, run the following command:

`pnpm exec nx test @smart-prescription-reader/infra --configuration=update-snapshot`

## Run lint

Run `pnpm exec nx lint @smart-prescription-reader/infra`

### Fixable issues

You can also automatically fix some lint errors by running the following command:

`pnpm exec nx lint @smart-prescription-reader/infra --configuration=fix`

## Deploy to AWS

### Deploy all Stacks

Run `pnpm exec nx deploy @smart-prescription-reader/infra --all`

### Deploy a single Stack

Run `pnpm exec nx deploy @smart-prescription-reader/infra [stackName]`

### Hotswap deployment

> [!CAUTION]
> Not to be used in production deployments

Use the --hotswap flag with the deploy target to attempt to update your AWS resources directly instead of generating an AWS CloudFormation change set and deploying it. Deployment falls back to AWS CloudFormation deployment if hot swapping is not possible.

Currently hot swapping supports Lambda functions, Step Functions state machines, and Amazon ECS container images. The --hotswap flag also disables rollback (i.e., implies --no-rollback).

Run `pnpm exec nx deploy @smart-prescription-reader/infra --hotswap --all`

## Cfn Guard Suppressions

There may be instances where you want to suppress certain rules on resources. You can do this in two ways:

### Supress a rule on a given construct

```typescript
import { suppressRule } from ':smart-prescription-reader/common-constructs';

...
// suppresses the RULE_NAME for the given construct.
suppressRule(construct, 'RULE_NAME');
```

### Supress a rule on a descendant construct

```typescript
import { suppressRule } from ':smart-prescription-reader/common-constructs';

...
// Supresses the RULE_NAME for the construct or any of its descendants if it is an instance of Bucket
suppressRule(construct, 'RULE_NAME', (construct) => construct instanceof Bucket);
```

## Useful links

- [Infra reference docs](TODO)
- [Learn more about NX](https://nx.dev/getting-started/intro)
