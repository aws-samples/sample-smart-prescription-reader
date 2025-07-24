/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import {
  ArnFormat,
  aws_ec2 as ec2,
  aws_iam as iam,
  aws_lambda as lambda,
  aws_logs as logs,
  aws_s3 as s3,
  CfnOutput,
  Duration,
  RemovalPolicy,
  Stack,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { NagSuppressions } from 'cdk-nag';
import { SmartPrescriptionReaderCode } from '../../smartPrescriptionReaderCode.js';

export interface EvaluateResponseProps {
  readonly imagesBucket: s3.IBucket;
  readonly configBucket: s3.IBucket;
  readonly bedrockPolicy: iam.IManagedPolicy;
  readonly ssmParameterPrefix: string;
  readonly vpc: ec2.IVpc;
}

export class EvaluateResponse extends lambda.Function {
  constructor(scope: Construct, id: string, props: EvaluateResponseProps) {
    const configParam = '/EvaluateResponseLambdaConfig';

    const evaluateResponseLogs = new logs.LogGroup(
      scope,
      'EvaluateResponseLogs',
      {
        retention: logs.RetentionDays.ONE_MONTH,
        removalPolicy: RemovalPolicy.DESTROY,
      },
    );

    super(scope, id, {
      runtime: lambda.Runtime.PYTHON_3_13,
      architecture: lambda.Architecture.ARM_64,
      handler:
        'smart_prescription_reader.lambda_handlers.evaluate_response.handler',
      code: SmartPrescriptionReaderCode.getInstance(),
      environment: {
        INPUT_BUCKET_NAME: props.imagesBucket.bucketName,
        CONFIG_BUCKET_NAME: props.configBucket.bucketName,
        CONFIG_PARAM: props.ssmParameterPrefix + configParam,
      },
      timeout: Duration.seconds(60),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      logGroup: evaluateResponseLogs,
    });

    props.imagesBucket.grantRead(this);
    props.configBucket.grantRead(this);

    this.role?.addManagedPolicy(props.bedrockPolicy);

    this.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['ssm:GetParameter'],
        resources: [
          Stack.of(this).formatArn({
            arnFormat: ArnFormat.SLASH_RESOURCE_NAME,
            service: 'ssm',
            resource: 'parameter',
            resourceName: props.ssmParameterPrefix.slice(1) + configParam,
          }),
        ],
      }),
    );

    NagSuppressions.addResourceSuppressions(
      this,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'AWSLambdaBasicExecutionRole to expedite development. Consider replacing in production',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Wildcard to allow reading any objects in specific buckets and invoking any model in Bedrock.',
        },
      ],
      true,
    );

    new CfnOutput(this, 'EvaluateResponseLambdaConfig', {
      value: props.ssmParameterPrefix + configParam,
    });
  }
}
