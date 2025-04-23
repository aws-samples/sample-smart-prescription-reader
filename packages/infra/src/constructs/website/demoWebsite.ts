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
  aws_s3 as s3,
  aws_s3_deployment as s3deploy,
  Stack,
} from 'aws-cdk-lib';
import { UserIdentity } from ':smart-prescription-reader/common-constructs';
import { Construct } from 'constructs';
import { IRuntimeConfig } from ':smart-prescription-reader/common-types';

export interface DemoWebsiteProps {
  readonly api: appsync.GraphqlApi;
  readonly userIdentity: UserIdentity;
  readonly inputBucket: s3.IBucket;
  readonly configBucket: s3.IBucket;
}

export class DemoWebsite extends Construct {
  public readonly websiteUrl: string;

  constructor(scope: Construct, id: string, props: DemoWebsiteProps) {
    super(scope, id);
    const runtimeConfig: IRuntimeConfig = {
      cognitoProps: {
        region: Stack.of(this).region,
        identityPoolId: props.userIdentity.identityPool.identityPoolId,
        userPoolId: props.userIdentity.userPool?.userPoolId,
        userPoolWebClientId:
          props.userIdentity.userPoolClient?.userPoolClientId,
      },
      graphqlEndpoint: props.api.graphqlUrl,
      inputBucket: props.inputBucket.bucketName,
    };

    new s3deploy.BucketDeployment(this, 'RuntimeConfig', {
      sources: [s3deploy.Source.jsonData('runtime-config.json', runtimeConfig)],
      destinationBucket: props.configBucket,
      destinationKeyPrefix: 'frontend/',
    });

    this.websiteUrl = 'See packages/demo/README.md';
  }
}
