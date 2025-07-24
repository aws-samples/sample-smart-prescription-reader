/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import {
  aws_ec2 as ec2,
  aws_iam as iam,
  aws_lambda as lambda,
  aws_logs as logs,
  aws_s3 as s3,
  Duration,
  RemovalPolicy,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { NagSuppressions } from 'cdk-nag';
import { SmartPrescriptionReaderCode } from '../../smartPrescriptionReaderCode.js';

export interface OcrPrescriptionProps {
  readonly imagesBucket: s3.IBucket;
  readonly vpc: ec2.IVpc;
}

export class OcrPrescription extends lambda.Function {
  constructor(scope: Construct, id: string, props: OcrPrescriptionProps) {
    const ocrPrescriptionLogs = new logs.LogGroup(
      scope,
      'OcrPrescriptionLogs',
      {
        retention: logs.RetentionDays.ONE_MONTH,
        removalPolicy: RemovalPolicy.DESTROY,
      },
    );

    super(scope, id, {
      runtime: lambda.Runtime.PYTHON_3_13,
      architecture: lambda.Architecture.ARM_64,
      handler: 'smart_prescription_reader.lambda_handlers.ocr.handler',
      code: SmartPrescriptionReaderCode.getInstance(),
      environment: {
        INPUT_BUCKET_NAME: props.imagesBucket.bucketName,
      },
      timeout: Duration.seconds(60),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      logGroup: ocrPrescriptionLogs,
    });

    props.imagesBucket.grantRead(this);

    // Add Textract permissions
    this.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['textract:DetectDocumentText'],
        resources: ['*'],
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
            'Wildcard to allow reading any objects in specific buckets and using Textract.',
        },
      ],
      true,
    );
  }
}
