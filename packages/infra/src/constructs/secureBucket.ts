/*
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import { aws_s3 as s3, Duration, RemovalPolicy, Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';

export class AccessLogsBucket {
  public static getLogsBucket(
    scope: Construct,
    constructId = 'AccessLogsBucket',
  ): s3.Bucket {
    if (!AccessLogsBucket.bucket) {
      AccessLogsBucket.bucket = new s3.Bucket(Stack.of(scope), constructId, {
        versioned: true,
        removalPolicy: RemovalPolicy.RETAIN, // Retain logs even if stack is destroyed
        objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        encryption: s3.BucketEncryption.S3_MANAGED,
        enforceSSL: true,
        lifecycleRules: [
          {
            enabled: true,
            expiration: Duration.days(365), // Adjust retention period as needed
          },
        ],
      });
    }
    return AccessLogsBucket.bucket;
  }

  private static bucket: s3.Bucket;

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  private constructor() {} // Prevent direct instantiation
}

export class SecureBucket extends s3.Bucket {
  constructor(scope: Construct, id: string, props: s3.BucketProps) {
    const accessLogsBucket = AccessLogsBucket.getLogsBucket(scope);
    super(scope, id, {
      versioned: true,
      serverAccessLogsBucket: accessLogsBucket,
      serverAccessLogsPrefix: `${id}/`,
      removalPolicy: RemovalPolicy.DESTROY,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      lifecycleRules: [
        {
          enabled: true,
          expiration: Duration.days(90),
        },
      ],
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,
      ...props,
    });
  }
}
