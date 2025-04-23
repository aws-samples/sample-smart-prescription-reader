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
  aws_dynamodb as ddb,
  aws_ec2 as ec2,
  aws_iam as iam,
  aws_kms as kms,
  aws_logs as logs,
  aws_s3 as s3,
  aws_stepfunctions as sfn,
  aws_stepfunctions_tasks as tasks,
  Duration,
  Names,
  RemovalPolicy,
  Stack,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { NagSuppressions } from 'cdk-nag';
import { ExtractPrescription } from './taskFunctions/extractPrescription.js';
import { EvaluateResponse } from './taskFunctions/evaluateResponse.js';
import { CorrectResponse } from './taskFunctions/correctResponse.js';
import { UpdateJobStatus } from './taskFunctions/updateJobStatus.js';
import { OcrPrescription } from './taskFunctions/ocrPrescription.js';

export interface SmartPrescriptionReaderWorkflowProps {
  readonly inputBucket: s3.IBucket;
  readonly configBucket: s3.IBucket;
  readonly jobStatusTable: ddb.ITableV2;
  readonly ssmParameterPrefix: string;
  readonly bedrockPolicy: iam.IManagedPolicy;
  readonly maxCorrections: number;
  readonly vpc: ec2.IVpc;
}

/**
 * A state machine that orchestrates the workflow of extracting a prescription from an image,
 * evaluating the response, and updating the job status.
 *
 * The state machine is integrated with the AppSync API to update the job status.
 *
 * Example input event:
 * {
 *   "jobId": "12345",
 *   "image": "/path/image.jpg",
 *   "prescriptionSchema": "{...}",
 *   "temperature": 0.0,
 *   "fastModel": "us.anthropic.claude-3-haiku-20240307-v1:0",
 *   "judgeModel": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
 *   "powerfulModel": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
 *   "useTextract": true
 * }
 */
export class SmartPrescriptionReaderWorkflow extends Construct {
  readonly workflow: sfn.StateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: SmartPrescriptionReaderWorkflowProps,
  ) {
    super(scope, id);

    const ocrPrescriptionLambda = new OcrPrescription(
      this,
      'OcrPrescriptionLambda',
      {
        imagesBucket: props.inputBucket,
        vpc: props.vpc,
      },
    );

    const extractPrescriptionLambda = new ExtractPrescription(
      this,
      'ExtractPrescriptionLambda',
      {
        ssmParameterPrefix: props.ssmParameterPrefix,
        bedrockPolicy: props.bedrockPolicy,
        imagesBucket: props.inputBucket,
        configBucket: props.configBucket,
        vpc: props.vpc,
      },
    );

    const evaluateResponseLambda = new EvaluateResponse(
      this,
      'EvaluateResponseLambda',
      {
        ssmParameterPrefix: props.ssmParameterPrefix,
        bedrockPolicy: props.bedrockPolicy,
        imagesBucket: props.inputBucket,
        configBucket: props.configBucket,
        vpc: props.vpc,
      },
    );

    const correctResponseLambda = new CorrectResponse(
      this,
      'CorrectResponseLambda',
      {
        ssmParameterPrefix: props.ssmParameterPrefix,
        bedrockPolicy: props.bedrockPolicy,
        imagesBucket: props.inputBucket,
        configBucket: props.configBucket,
        vpc: props.vpc,
      },
    );

    const updateJobStatusLambda = new UpdateJobStatus(
      this,
      'UpdateJobStatusLambda',
      {
        jobStatusTable: props.jobStatusTable,
        vpc: props.vpc,
      },
    );

    const catchHandler = sfn.Pass.jsonata(this, 'CatchHandler', {
      assign: {
        errorMessage: 'Internal error',
        errorCode: 'InternalError',
      },
    });

    const updateStatusFailed = tasks.LambdaInvoke.jsonata(
      this,
      'UpdateStatusFailed',
      {
        lambdaFunction: updateJobStatusLambda,
        payload: sfn.TaskInput.fromObject({
          jobId: '{% $jobId %}',
          status: 'FAILED',
          error: `{% { "message": $errorMessage, "code": $errorCode } %}`,
          usage: '{% $exists($usage) and $usage != null ? [$usage] : [] %}',
        }),
      },
    );

    catchHandler.next(updateStatusFailed);

    updateStatusFailed.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });

    const storeInputs = sfn.Pass.jsonata(this, 'StoreInputs', {
      assign: {
        jobId: '{% $states.input.jobId %}',
        image: '{% $states.input.image %}',
        prescriptionSchema: '{% $states.input.prescriptionSchema %}',
        temperature:
          '{% $exists($states.input.temperature) ? $states.input.temperature : null %}',
        fastModel:
          '{% $exists($states.input.fastModel) ? $states.input.fastModel: null %}',
        judgeModel:
          '{% $exists($states.input.judgeModel) ? $states.input.judgeModel : null %}',
        powerfulModel:
          '{% $exists($states.input.powerfulModel) ? $states.input.powerfulModel : null %}',
        useTextract:
          '{% $exists($states.input.useTextract) ? $states.input.useTextract : true %}',
        correctionCount: 0,
        maxCorrections: `{% $exists($states.input.maxCorrections) ? $states.input.maxCorrections : ${props.maxCorrections} %}`,
      },
    });

    const shouldOcr = sfn.Choice.jsonata(this, 'ShouldOcr');

    const updateStatusOcr = tasks.LambdaInvoke.jsonata(
      this,
      'UpdateStatusOcr',
      {
        lambdaFunction: updateJobStatusLambda,
        payload: sfn.TaskInput.fromObject({
          jobId: '{% $jobId %}',
          status: 'PROCESSING',
          state: 'TRANSCRIBE',
        }),
      },
    );
    updateStatusOcr.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    updateStatusOcr.addCatch(catchHandler, {});

    const ocrPrescription = tasks.LambdaInvoke.jsonata(
      this,
      'OcrPrescription',
      {
        lambdaFunction: ocrPrescriptionLambda,
        payload: sfn.TaskInput.fromObject({
          image: '{% $image %}',
        }),
        assign: {
          ocrText: '{% $states.result.Payload.transcription %}',
        },
      },
    );

    ocrPrescription.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    ocrPrescription.addCatch(catchHandler, {});

    const updateStatusProcessing = tasks.LambdaInvoke.jsonata(
      this,
      'UpdateStatusProcessing',
      {
        lambdaFunction: updateJobStatusLambda,
        payload: sfn.TaskInput.fromObject({
          jobId: '{% $jobId %}',
          status: 'PROCESSING',
          state: 'EXTRACT',
        }),
        assign: {
          usage: '{% null %}',
        },
      },
    );
    updateStatusProcessing.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    updateStatusProcessing.addCatch(catchHandler, {});

    const extractPrescription = tasks.LambdaInvoke.jsonata(
      this,
      'ExtractPrescription',
      {
        lambdaFunction: extractPrescriptionLambda,
        payload: sfn.TaskInput.fromObject({
          image: '{% $image %}',
          prescriptionSchema: '{% $prescriptionSchema %}',
          temperature: '{% $temperature %}',
          model: '{% $fastModel %}',
          ocrTranscription: '{% $ocrText ? $ocrText : null %}',
        }),
        assign: {
          isHandwritten: '{% $states.result.Payload.isHandwritten %}',
          isPrescription: '{% $states.result.Payload.isPrescription %}',
          extraction: '{% $states.result.Payload.extraction %}',
          usage: '{% $states.result.Payload.usage %}',
        },
      },
    );

    extractPrescription.addRetry({
      errors: ['RateLimitError'],
      maxAttempts: 3,
      backoffRate: 2,
      interval: Duration.seconds(30),
      maxDelay: Duration.seconds(60),
    });
    extractPrescription.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    extractPrescription.addCatch(catchHandler, {});

    const isPrescription = sfn.Choice.jsonata(this, 'IsPrescription', {
      assign: {
        errorCode: "{% $isPrescription ? null : 'InvalidImage' %}",
        errorMessage:
          "{% $isPrescription ? null : 'The image does not contain a prescription.' %}",
      },
    });

    const updateStatusJudge = tasks.LambdaInvoke.jsonata(
      this,
      'UpdateStatusJudge',
      {
        lambdaFunction: updateJobStatusLambda,
        payload: sfn.TaskInput.fromObject({
          jobId: '{% $jobId %}',
          status: 'PROCESSING',
          state: 'JUDGE',
          usage: '{% [$usage] %}',
        }),
        assign: {
          usage: '{% null %}',
        },
      },
    );
    updateStatusJudge.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    updateStatusJudge.addCatch(catchHandler, {});

    const evaluateResponse = tasks.LambdaInvoke.jsonata(
      this,
      'EvaluateResponse',
      {
        lambdaFunction: evaluateResponseLambda,
        payload: sfn.TaskInput.fromObject({
          image: '{% $image %}',
          prescriptionSchema: '{% $prescriptionSchema %}',
          temperature: '{% $temperature %}',
          model: '{% $judgeModel %}',
          extraction: '{% $extraction %}',
          ocrTranscription: '{% $ocrText ? $ocrText : null %}',
        }),
        assign: {
          score: '{% $uppercase($states.result.Payload.score) %}',
          feedback: '{% $states.result.Payload.feedback %}',
          usage: '{% $states.result.Payload.usage %}',
          shouldCorrect:
            '{% $uppercase($states.result.Payload.score) in ["POOR", "FAIR"] and $correctionCount < $maxCorrections %}',
        },
      },
    );
    evaluateResponse.addRetry({
      errors: ['RateLimitError'],
      maxAttempts: 3,
      backoffRate: 2,
      interval: Duration.seconds(30),
      maxDelay: Duration.seconds(60),
    });
    evaluateResponse.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    evaluateResponse.addCatch(catchHandler, {});

    const shouldCorrect = sfn.Choice.jsonata(this, 'ShouldCorrect', {});

    const updateStatusCorrect = tasks.LambdaInvoke.jsonata(
      this,
      'UpdateStatusCorrect',
      {
        lambdaFunction: updateJobStatusLambda,
        payload: sfn.TaskInput.fromObject({
          jobId: '{% $jobId %}',
          status: 'PROCESSING',
          state: 'CORRECT',
          usage: '{% [$usage] %}',
          score: '{% $score %}',
        }),
        assign: {
          usage: '{% null %}',
          correctionCount: '{% $correctionCount + 1 %}',
        },
      },
    );

    updateStatusCorrect.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    updateStatusCorrect.addCatch(catchHandler, {});

    const correctResponse = tasks.LambdaInvoke.jsonata(
      this,
      'CorrectResponse',
      {
        lambdaFunction: correctResponseLambda,
        payload: sfn.TaskInput.fromObject({
          image: '{% $image %}',
          prescriptionSchema: '{% $prescriptionSchema %}',
          temperature: '{% $temperature %}',
          model: '{% $powerfulModel %}',
          extraction: '{% $extraction %}',
          feedback: '{% $feedback %}',
          ocrTranscription: '{% $ocrText ? $ocrText : null %}',
        }),
        assign: {
          extraction: '{% $states.result.Payload.extraction %}',
          usage: '{% $states.result.Payload.usage %}',
        },
      },
    );
    correctResponse.addRetry({
      errors: ['RateLimitError'],
      maxAttempts: 3,
      backoffRate: 2,
      interval: Duration.seconds(30),
      maxDelay: Duration.seconds(60),
    });
    correctResponse.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    correctResponse.addCatch(catchHandler, {});

    const updateStatusCompleted = tasks.LambdaInvoke.jsonata(
      this,
      'UpdateStatusCompleted',
      {
        lambdaFunction: updateJobStatusLambda,
        payload: sfn.TaskInput.fromObject({
          jobId: '{% $jobId %}',
          status: 'COMPLETED',
          prescriptionData: '{% $extraction %}',
          score: '{% $score %}',
          message: '{% $feedback %}',
          usage: '{% [$usage] %}',
        }),
        assign: {
          usage: '{% null %}',
        },
      },
    );
    updateStatusCompleted.addRetry({
      errors: ['States.ALL'],
      maxAttempts: 3,
    });
    updateStatusCompleted.addCatch(catchHandler, {});

    const success = sfn.Succeed.jsonata(this, 'Success', {
      outputs: {
        prescriptionData: '{% $extraction %}',
        score: '{% $score %}',
        feedback: '{% $feedback %}',
      },
    });

    const failed = sfn.Fail.jsonata(this, 'Fail', {});

    const chain = storeInputs.next(shouldOcr);
    shouldOcr
      .when(sfn.Condition.jsonata('{% $useTextract %}'), updateStatusOcr)
      .otherwise(updateStatusProcessing);

    updateStatusOcr.next(ocrPrescription).next(updateStatusProcessing);
    updateStatusProcessing.next(extractPrescription).next(isPrescription);

    isPrescription
      .when(sfn.Condition.jsonata('{% $isPrescription %}'), updateStatusJudge)
      .otherwise(updateStatusFailed);

    updateStatusFailed.next(failed);

    updateStatusJudge.next(evaluateResponse).next(shouldCorrect);

    shouldCorrect
      .when(sfn.Condition.jsonata('{% $shouldCorrect %}'), updateStatusCorrect)
      .otherwise(updateStatusCompleted);

    updateStatusCorrect.next(correctResponse).next(updateStatusJudge);

    updateStatusCompleted.next(success);

    const logGroupName = Names.uniqueResourceName(this, {
      maxLength: 32,
    });
    const logKey = new kms.Key(this, 'LogGroupKey', {
      enableKeyRotation: true,
      description: 'step functions log group',
      removalPolicy: RemovalPolicy.DESTROY,
    });

    /**
     * Required KMS key policy which allows the CloudWatchLogs service principal to encrypt the entire log group using the
     * customer managed kms key. See: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html#cmk-permissions
     */
    logKey.addToResourcePolicy(
      new iam.PolicyStatement({
        resources: ['*'],
        actions: [
          'kms:Encrypt*',
          'kms:Decrypt*',
          'kms:ReEncrypt*',
          'kms:GenerateDataKey*',
          'kms:Describe*',
        ],
        principals: [
          new iam.ServicePrincipal(
            `logs.${Stack.of(this).region}.amazonaws.com`,
          ),
        ],
        conditions: {
          ArnEquals: {
            'kms:EncryptionContext:aws:logs:arn': Stack.of(this).formatArn({
              service: 'logs',
              resource: 'log-group',
              resourceName: `/aws/vendedlogs/states/${logGroupName}`,
              arnFormat: ArnFormat.COLON_RESOURCE_NAME,
            }),
          },
        },
      }),
    );
    const logGroup = new logs.LogGroup(this, 'LogGroup', {
      retention: logs.RetentionDays.ONE_MONTH,
      logGroupName: `/aws/vendedlogs/states/${logGroupName}`,
      removalPolicy: RemovalPolicy.DESTROY,
      encryptionKey: logKey,
    });

    const workflowKey = new kms.Key(this, 'WorkflowKey', {
      enableKeyRotation: true,
      description: 'step functions workflow',
      removalPolicy: RemovalPolicy.DESTROY,
    });

    this.workflow = new sfn.StateMachine(this, 'Workflow', {
      stateMachineType: sfn.StateMachineType.EXPRESS,
      queryLanguage: sfn.QueryLanguage.JSONATA,
      tracingEnabled: true,
      definitionBody: sfn.DefinitionBody.fromChainable(chain),
      logs: {
        destination: logGroup,
        level: sfn.LogLevel.ALL,
        includeExecutionData: true,
      },
      encryptionConfiguration: new sfn.CustomerManagedEncryptionConfiguration(
        workflowKey,
      ),
    });

    this.workflow.role.attachInlinePolicy(
      new iam.Policy(this, 'WorkflowLogEncryptionPolicy', {
        statements: [
          new iam.PolicyStatement({
            conditions: {
              StringEquals: {
                'kms:EncryptionContext:aws:states:stateMachineArn':
                  this.workflow.stateMachineArn,
              },
            },
            actions: ['kms:Decrypt', 'kms:GenerateDataKey'],
            resources: [workflowKey.keyArn],
            effect: iam.Effect.ALLOW,
          }),
        ],
      }),
    );

    NagSuppressions.addResourceSuppressions(
      this.workflow,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Wildcard to allow writing to logs',
        },
      ],
      true,
    );
  }
}
