import { util } from '@aws-appsync/utils';

export function request(ctx) {
  const jobId = ctx.args.jobId;

  return {
    operation: 'GetItem',
    key: util.dynamodb.toMapValues({ jobId }),
    consistentRead: true,
  };
}

export function response(ctx) {
  // Check authentication type and set appropriate conditions
  if (ctx.identity.issuer) {
    // AWS_COGNITO_USER_POOLS auth
    if (!ctx.identity.username) {
      util.unauthorized();
    }
    if (ctx.result && ctx.result.owner !== ctx.identity.username) {
      util.unauthorized();
    }
  }

  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }

  // Handle case where item doesn't exist
  if (!ctx.result) {
    util.error('Job not found', 'NotFound');
  }

  return ctx.result;
}
