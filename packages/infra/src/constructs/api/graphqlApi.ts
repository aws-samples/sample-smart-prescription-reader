/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import {
  aws_appsync as appsync,
  aws_cognito as cognito,
  aws_dynamodb as dynamodb,
  aws_kms as kms,
  aws_logs as logs,
  aws_wafv2 as wafv2,
  RemovalPolicy,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as path from 'node:path';
import { workspaceRoot } from '@nx/devkit';
import { NagSuppressions } from 'cdk-nag';

export interface GraphqlApiProps {
  readonly userPool: cognito.IUserPool;
}

export class GraphqlApi extends Construct {
  readonly jobsTable: dynamodb.TableV2;
  readonly jobsTableKey: kms.Key;
  readonly api: appsync.GraphqlApi;

  constructor(scope: Construct, id: string, props: GraphqlApiProps) {
    super(scope, id);

    this.jobsTableKey = new kms.Key(this, 'JobsTableKey', {
      enableKeyRotation: true,
      description: 'jobs table',
      removalPolicy: RemovalPolicy.DESTROY,
    });

    this.jobsTable = new dynamodb.TableV2(this, 'JobsTable', {
      partitionKey: {
        name: 'jobId',
        type: dynamodb.AttributeType.STRING,
      },
      billing: dynamodb.Billing.onDemand(),
      removalPolicy: RemovalPolicy.DESTROY,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
        recoveryPeriodInDays: 7,
      },
      timeToLiveAttribute: 'ttl',
      encryption: dynamodb.TableEncryptionV2.customerManagedKey(
        this.jobsTableKey,
      ),
    });

    this.api = new appsync.GraphqlApi(this, 'Api', {
      name: 'SmartPrescriptionReader',
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: appsync.AuthorizationType.USER_POOL,
          userPoolConfig: {
            userPool: props.userPool,
          },
        },
        additionalAuthorizationModes: [
          {
            authorizationType: appsync.AuthorizationType.IAM,
          },
        ],
      },
      definition: appsync.Definition.fromFile(
        path.join(
          workspaceRoot,
          'packages/common/models-graphql/src/schema/schema.graphql',
        ),
      ),
      xrayEnabled: true,
      logConfig: {
        fieldLogLevel: appsync.FieldLogLevel.INFO,
        retention: logs.RetentionDays.ONE_MONTH, // TODO: choose something that fits your auditing needs
      },
    });

    const apiLogsRole = this.api.node
      .findAll()
      .find((c) => c.node.path.endsWith('ApiLogsRole'));
    if (apiLogsRole) {
      NagSuppressions.addResourceSuppressions(apiLogsRole, [
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'Using the CDK default managed policy for AppSync to push logs to CloudWatch Logs to expedite development.',
        },
      ]);
    }

    const waf = new wafv2.CfnWebACL(this, 'WebAcl', {
      defaultAction: { allow: {} },
      scope: 'REGIONAL',
      visibilityConfig: {
        cloudWatchMetricsEnabled: true,
        metricName: 'WebAcl',
        sampledRequestsEnabled: true,
      },
      rules: [
        {
          name: 'CRSRule',
          priority: 0,
          statement: {
            managedRuleGroupStatement: {
              name: 'AWSManagedRulesCommonRuleSet',
              vendorName: 'AWS',
            },
          },
          visibilityConfig: {
            cloudWatchMetricsEnabled: true,
            metricName: 'MetricForWebACLCDK-CRS',
            sampledRequestsEnabled: true,
          },
          overrideAction: {
            none: {},
          },
        },
      ],
    });

    new wafv2.CfnWebACLAssociation(this, 'WebAclAssociation', {
      resourceArn: this.api.arn,
      webAclArn: waf.attrArn,
    });
  }
}
