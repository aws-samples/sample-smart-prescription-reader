/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import {
  aws_dynamodb as ddb,
  aws_ec2 as ec2,
  aws_lambda as lambda,
  aws_logs as logs,
  RemovalPolicy,
  Duration,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { NagSuppressions } from 'cdk-nag';
import { SmartPrescriptionReaderCode } from '../../smartPrescriptionReaderCode.js';

export interface UpdateJobStatusProps {
  readonly jobStatusTable: ddb.ITableV2;
  readonly vpc: ec2.IVpc;
}

export class UpdateJobStatus extends lambda.Function {
  constructor(scope: Construct, id: string, props: UpdateJobStatusProps) {
    const updateJobStatusLogs = new logs.LogGroup(
      scope,
      'UpdateJobStatusLogs',
      {
        retention: logs.RetentionDays.ONE_MONTH,
        removalPolicy: RemovalPolicy.DESTROY,
      },
    );

    super(scope, id, {
      runtime: lambda.Runtime.PYTHON_3_13,
      architecture: lambda.Architecture.ARM_64,
      handler:
        'smart_prescription_reader.lambda_handlers.update_job_status.handler',
      code: SmartPrescriptionReaderCode.getInstance(),
      environment: {
        JOB_STATUS_TABLE: props.jobStatusTable.tableName,
      },
      timeout: Duration.seconds(60),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      logGroup: updateJobStatusLogs,
    });

    props.jobStatusTable.grantReadWriteData(this);

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
          reason: 'Wildcard to allow encryption with KMS CMK.',
          appliesTo: ['Action::kms:GenerateDataKey*', 'Action::kms:ReEncrypt*'],
        },
      ],
      true,
    );
  }
}
