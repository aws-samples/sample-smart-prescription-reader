/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */
import { aws_iam as iam, Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {
  BedrockFoundationModel,
  CrossRegionInferenceProfile,
  REGION_TO_GEO_AREA,
} from '@cdklabs/generative-ai-cdk-constructs/lib/cdk-lib/bedrock';
import { NagSuppressions } from 'cdk-nag';

export class BedrockPolicy extends iam.ManagedPolicy {
  constructor(scope: Construct, id: string) {
    super(scope, id);

    const allModels = new BedrockFoundationModel('*', {
      supportsAgents: true,
      supportsCrossRegion: true,
    });
    allModels.grantInvokeAllRegions(this);

    const crisAllModels = CrossRegionInferenceProfile.fromConfig({
      model: allModels,
      geoRegion: REGION_TO_GEO_AREA[Stack.of(this).region],
    });

    crisAllModels.grantInvoke(this);

    NagSuppressions.addResourceSuppressions(
      this,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Wildcard to allow invoking any model in Bedrock.',
        },
      ],
      true,
    );
  }
}
