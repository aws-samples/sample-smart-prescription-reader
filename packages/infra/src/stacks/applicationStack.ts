/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */
import {
  Aws,
  aws_ec2 as ec2,
  aws_iam as iam,
  aws_kms as kms,
  aws_logs as logs,
  aws_s3 as s3,
  CfnOutput,
  Duration,
  RemovalPolicy,
  Stack,
  StackProps,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { UserIdentity } from ':smart-prescription-reader/common-constructs';
import { NagSuppressions } from 'cdk-nag';
import { SecureBucket } from '../constructs/secureBucket.js';
import { GraphqlApi } from '../constructs/api/graphqlApi.js';
import { SmartPrescriptionReaderWorkflow } from '../constructs/workflow/smartPrescriptionReaderWorkflow.js';
import { AppSyncDataSources } from '../constructs/api/appSyncDataSources.js';
import { BedrockPolicy } from '../constructs/bedrockPolicy.js';
import { DemoWebsite } from '../constructs/website/demoWebsite.js';

export class ApplicationStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const ssmParameterPrefix = `/${Aws.STACK_NAME}`;

    const flowLogs = new logs.LogGroup(this, 'FlowLogs', {
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const vpc = new ec2.Vpc(this, 'Vpc', {
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        {
          name: 'isolated',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
      flowLogs: {
        VpcFlowLogs: {
          destination: ec2.FlowLogDestination.toCloudWatchLogs(flowLogs),
        },
      },
    });

    const bedrockRuntimeInterface = vpc.addInterfaceEndpoint(
      'BedrockRuntimeInterface',
      {
        service: new ec2.InterfaceVpcEndpointAwsService('bedrock-runtime'),
      },
    );

    const ssmInterface = vpc.addInterfaceEndpoint('SsmInterface', {
      service: new ec2.InterfaceVpcEndpointAwsService('ssm'),
    });

    const textractInterface = vpc.addInterfaceEndpoint('TextractInterface', {
      service: new ec2.InterfaceVpcEndpointAwsService('textract'),
    });

    NagSuppressions.addResourceSuppressions(
      bedrockRuntimeInterface,
      [
        {
          id: 'AwsSolutions-EC23',
          reason:
            'cdk nag error. Security group allows inbound access on port 443 from the VPC.',
        },
      ],
      true,
    );

    NagSuppressions.addResourceSuppressions(
      ssmInterface,
      [
        {
          id: 'AwsSolutions-EC23',
          reason:
            'cdk nag error. Security group allows inbound access on port 443 from the VPC.',
        },
      ],
      true,
    );

    NagSuppressions.addResourceSuppressions(
      textractInterface,
      [
        {
          id: 'AwsSolutions-EC23',
          reason:
            'cdk nag error. Security group allows inbound access on port 443 from the VPC.',
        },
      ],
      true,
    );

    vpc.addGatewayEndpoint('dynamodb', {
      service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
    });
    const s3Gateway = vpc.addGatewayEndpoint('s3', {
      service: ec2.GatewayVpcEndpointAwsService.S3,
    });

    const bedrockPolicy = new BedrockPolicy(this, 'BedrockPolicy');

    const imagesBucketKey = new kms.Key(this, 'ImagesBucketKey', {
      enableKeyRotation: true,
      description: 'images bucket',
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const imagesBucket = new SecureBucket(this, 'ImagesBucket', {
      lifecycleRules: [
        {
          enabled: true,
          expiration: Duration.days(1), // Adjust retention period as needed
        },
      ],
      cors: [
        {
          allowedHeaders: ['content-type'],
          allowedOrigins: ['http://localhost:4200'],
          allowedMethods: [
            s3.HttpMethods.GET,
            s3.HttpMethods.PUT,
            s3.HttpMethods.HEAD,
          ],
        },
      ],
      encryptionKey: imagesBucketKey,
      encryption: s3.BucketEncryption.KMS,
    });

    imagesBucket.addToResourcePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.DENY,
        actions: ['s3:GetObject'],
        resources: [imagesBucket.arnForObjects('*')],
        principals: [new iam.AnyPrincipal()],
        conditions: {
          StringNotEquals: {
            'aws:SourceVpce': s3Gateway.vpcEndpointId,
          },
          Bool: {
            'aws:ViaAWSService': false,
          },
        },
      }),
    );

    const configBucket = new SecureBucket(this, 'ConfigBucket', {
      lifecycleRules: [],
    });

    const userIdentity = new UserIdentity(this, 'UserIdentity');

    NagSuppressions.addResourceSuppressions(
      userIdentity.userPool,
      [
        {
          id: 'AwsSolutions-COG2',
          reason:
            'The Cognito User Pool is used for demo purposes only. In production, MFA should be required.',
        },
        {
          id: 'AwsSolutions-COG3',
          reason:
            'Advanced Security Features is deprecated in favor of the Plus feature plan.',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason: 'The Cognito SMS Role has wildcards to send SMS MFA tokens.',
        },
      ],
      true,
    );

    const api = new GraphqlApi(this, 'Api', {
      userPool: userIdentity.userPool,
    });

    const workflow = new SmartPrescriptionReaderWorkflow(this, 'Workflow', {
      inputBucket: imagesBucket,
      configBucket: configBucket,
      jobStatusTable: api.jobsTable,
      ssmParameterPrefix: ssmParameterPrefix,
      maxCorrections: 1,
      bedrockPolicy: bedrockPolicy,
      vpc: vpc,
    });

    new AppSyncDataSources(this, 'ApiDataSources', {
      api: api.api,
      jobsTable: api.jobsTable,
      workflow: workflow.workflow,
      imagesBucket: imagesBucket,
    });

    const website = new DemoWebsite(this, 'DemoWebsite', {
      api: api.api,
      userIdentity: userIdentity,
      inputBucket: imagesBucket,
      configBucket: configBucket,
    });

    NagSuppressions.addResourceSuppressionsByPath(
      Stack.of(this),
      `/${
        Stack.of(this).node.path
      }/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C`,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason: 'Managed upstream by AWS CDK',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Managed upstream by AWS CDK',
        },
        {
          id: 'AwsSolutions-L1',
          reason: 'Managed upstream by AWS CDK',
        },
      ],
      true,
    );

    new CfnOutput(this, 'UserIdentityPoolId', {
      value: userIdentity.userPool.userPoolId,
    });

    new CfnOutput(this, 'ImagesBucketName', {
      value: imagesBucket.bucketName,
    });

    new CfnOutput(this, 'ConfigBucketName', {
      value: configBucket.bucketName,
    });

    new CfnOutput(this, 'WebsiteUrl', {
      value: website.websiteUrl,
    });

    NagSuppressions.addResourceSuppressionsByPath(
      Stack.of(this),
      `/${
        Stack.of(this).node.path
      }/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a`,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason: 'Managed upstream by AWS CDK',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Managed upstream by AWS CDK',
        },
      ],
      true,
    );
  }
}
