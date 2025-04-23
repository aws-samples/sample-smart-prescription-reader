/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { Construct } from 'constructs';
import {
  aws_appsync as appsync,
  aws_dynamodb as ddb,
  aws_lambda as lambda,
  aws_logs as logs,
  aws_s3 as s3,
  aws_stepfunctions as sfn,
  Duration,
  RemovalPolicy,
} from 'aws-cdk-lib';
import path from 'node:path';
import { NagSuppressions } from 'cdk-nag';
import { fileURLToPath } from 'node:url';
import { SmartPrescriptionReaderCode } from '../smartPrescriptionReaderCode.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export interface AppSyncDataSourcesProps {
  readonly workflow: sfn.IStateMachine;
  readonly imagesBucket: s3.IBucket;
  readonly api: appsync.IGraphqlApi;
  readonly jobsTable: ddb.ITableV2;
}

export class AppSyncDataSources extends Construct {
  constructor(scope: Construct, id: string, props: AppSyncDataSourcesProps) {
    super(scope, id);

    const jobsDataSource = props.api.addDynamoDbDataSource(
      'JobsDataSource',
      props.jobsTable,
    );

    jobsDataSource.createResolver('GetJobStatusResolver', {
      typeName: 'Query',
      fieldName: 'getJobStatus',
      runtime: appsync.FunctionRuntime.JS_1_0_0,
      code: appsync.Code.fromAsset(
        path.join(__dirname, 'resolvers/getJobStatus.js'),
      ),
    });

    NagSuppressions.addResourceSuppressions(
      jobsDataSource,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Wildcard to allow encryption with KMS CMK.',
          appliesTo: ['Action::kms:GenerateDataKey*', 'Action::kms:ReEncrypt*'],
        },
      ],
      true,
    );

    const requestUploadFileLogs = new logs.LogGroup(
      this,
      'RequestUploadFileLogs',
      {
        retention: logs.RetentionDays.ONE_MONTH,
        removalPolicy: RemovalPolicy.DESTROY,
      },
    );

    const requestUploadFileFunction = new lambda.Function(
      this,
      'RequestUploadFileFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_13,
        architecture: lambda.Architecture.ARM_64,
        handler:
          'smart_prescription_reader.lambda_handlers.upload_file.handler',
        code: SmartPrescriptionReaderCode.getInstance(),
        environment: {
          INPUT_BUCKET_NAME: props.imagesBucket.bucketName,
        },
        timeout: Duration.seconds(15),
        logGroup: requestUploadFileLogs,
      },
    );

    props.imagesBucket.grantWrite(requestUploadFileFunction);

    const uploadFileDataSource = props.api.addLambdaDataSource(
      'UploadFileDataSource',
      requestUploadFileFunction,
    );

    uploadFileDataSource.createResolver('RequestUploadFileResolver', {
      typeName: 'Mutation',
      fieldName: 'requestUploadFile',
    });

    NagSuppressions.addResourceSuppressions(
      requestUploadFileFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Wildcards to allow to write to the input bucket and write to logs.',
        },
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'AWSLambdaBasicExecutionRole to expedite development. Consider replacing in production',
        },
      ],
      true,
    );

    NagSuppressions.addResourceSuppressions(
      uploadFileDataSource,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Wildcard to allow invocation of any version of the specific Lambda function.',
        },
      ],
      true,
    );

    const processPrescriptionLogs = new logs.LogGroup(
      this,
      'ProcessPrescriptionLogs',
      {
        retention: logs.RetentionDays.ONE_MONTH,
        removalPolicy: RemovalPolicy.DESTROY,
      },
    );

    const processPrescriptionFunction = new lambda.Function(
      this,
      'ProcessPrescriptionFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_13,
        architecture: lambda.Architecture.ARM_64,
        handler:
          'smart_prescription_reader.lambda_handlers.process_prescription.handler',
        code: SmartPrescriptionReaderCode.getInstance(),
        environment: {
          JOBS_TABLE: props.jobsTable.tableName,
          PRESCRIPTION_MACHINE: props.workflow.stateMachineArn,
        },
        timeout: Duration.seconds(15),
        logGroup: processPrescriptionLogs,
      },
    );

    props.jobsTable.grantWriteData(processPrescriptionFunction);
    props.workflow.grantStartExecution(processPrescriptionFunction);

    NagSuppressions.addResourceSuppressions(
      processPrescriptionFunction,
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

    const processPrescriptionDataSource = props.api.addLambdaDataSource(
      'ProcessPrescriptionDataSource',
      processPrescriptionFunction,
    );

    processPrescriptionDataSource.createResolver(
      'ProcessPrescriptionResolver',
      {
        typeName: 'Mutation',
        fieldName: 'processPrescription',
      },
    );

    NagSuppressions.addResourceSuppressions(
      processPrescriptionDataSource,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Wildcard to allow invocation of any version of the specific Lambda function.',
        },
      ],
      true,
    );
  }
}
