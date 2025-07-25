/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import { CfnJson, CfnOutput, RemovalPolicy, Stack, Token } from 'aws-cdk-lib';
import { Distribution, ViewerProtocolPolicy } from 'aws-cdk-lib/aws-cloudfront';
import { S3BucketOrigin } from 'aws-cdk-lib/aws-cloudfront-origins';
import {
  BlockPublicAccess,
  Bucket,
  BucketEncryption,
  IBucket,
  ObjectOwnership,
} from 'aws-cdk-lib/aws-s3';
import { BucketDeployment, Source } from 'aws-cdk-lib/aws-s3-deployment';
import { Construct } from 'constructs';
import { RuntimeConfig } from './runtime-config.js';
import { Key } from 'aws-cdk-lib/aws-kms';
import { CfnWebACL } from 'aws-cdk-lib/aws-wafv2';
const DEFAULT_RUNTIME_CONFIG_FILENAME = 'runtime-config.json';

export interface StaticWebsiteProps {
  readonly websiteFilePath: string;
}

/**
 * Deploys a Static Website using by default a private S3 bucket as an origin and Cloudfront as the entrypoint.
 *
 * This construct configures a webAcl containing rules that are generally applicable to web applications. This
 * provides protection against exploitation of a wide range of vulnerabilities, including some of the high risk
 * and commonly occurring vulnerabilities described in OWASP publications such as OWASP Top 10.
 *
 */
export class StaticWebsite extends Construct {
  public readonly websiteBucket: IBucket;
  public readonly cloudFrontDistribution: Distribution;
  public readonly bucketDeployment: BucketDeployment;

  constructor(
    scope: Construct,
    id: string,
    { websiteFilePath }: StaticWebsiteProps,
  ) {
    super(scope, id);
    this.node.setContext(
      '@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy',
      true,
    );

    const websiteKey = new Key(this, 'WebsiteKey', {
      enableKeyRotation: true,
    });

    const accessLogsBucket = new Bucket(this, 'AccessLogsBucket', {
      versioned: false,
      enforceSSL: true,
      autoDeleteObjects: true,
      removalPolicy: RemovalPolicy.DESTROY,
      encryption: BucketEncryption.KMS,
      encryptionKey: websiteKey,
      objectOwnership: ObjectOwnership.OBJECT_WRITER,
      publicReadAccess: false,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
    });
    // S3 Bucket to hold website files
    this.websiteBucket = new Bucket(this, 'WebsiteBucket', {
      versioned: true,
      enforceSSL: true,
      autoDeleteObjects: true,
      removalPolicy: RemovalPolicy.DESTROY,
      encryption: BucketEncryption.KMS,
      encryptionKey: websiteKey,
      objectOwnership: ObjectOwnership.BUCKET_OWNER_ENFORCED,
      publicReadAccess: false,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      serverAccessLogsPrefix: 'website-access-logs',
      serverAccessLogsBucket: accessLogsBucket,
    });
    // Web ACL
    const wafStack = new CloudfrontWebAcl(this, 'waf');

    // Cloudfront Distribution
    const logBucket = new Bucket(this, 'DistributionLogBucket', {
      enforceSSL: true,
      autoDeleteObjects: true,
      removalPolicy: RemovalPolicy.DESTROY,
      encryption: BucketEncryption.KMS,
      encryptionKey: websiteKey,
      objectOwnership: ObjectOwnership.BUCKET_OWNER_PREFERRED,
      publicReadAccess: false,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      serverAccessLogsPrefix: 'distribution-access-logs',
      serverAccessLogsBucket: accessLogsBucket,
    });
    const defaultRootObject = 'index.html';
    this.cloudFrontDistribution = new Distribution(
      this,
      'CloudfrontDistribution',
      {
        webAclId: wafStack.wafArn,
        enableLogging: true,
        logBucket: logBucket,
        defaultBehavior: {
          origin: S3BucketOrigin.withOriginAccessControl(this.websiteBucket),
          viewerProtocolPolicy: ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        },
        defaultRootObject,
        errorResponses: [
          {
            httpStatus: 404, // We need to redirect "key not found errors" to index.html for single page apps
            responseHttpStatus: 200,
            responsePagePath: `/${defaultRootObject}`,
          },
          {
            httpStatus: 403, // We need to redirect reloads from paths (e.g. /foo/bar) to index.html for single page apps
            responseHttpStatus: 200,
            responsePagePath: `/${defaultRootObject}`,
          },
        ],
      },
    );
    // Deploy Website
    this.bucketDeployment = new BucketDeployment(this, 'WebsiteDeployment', {
      sources: [
        Source.asset(websiteFilePath),
        Source.jsonData(
          DEFAULT_RUNTIME_CONFIG_FILENAME,
          this.resolveTokens(RuntimeConfig.ensure(this).config),
        ),
      ],
      destinationBucket: this.websiteBucket,
      // Files in the distribution's edge caches will be invalidated after files are uploaded to the destination bucket.
      distribution: this.cloudFrontDistribution,
    });
    new CfnOutput(this, 'DistributionDomainName', {
      value: this.cloudFrontDistribution.domainName,
    });
  }
  private resolveTokens = (payload: any) => {
    const _payload: Record<string, any> = {};
    Object.entries(payload).forEach(([key, value]) => {
      if (
        Token.isUnresolved(value) ||
        (typeof value === 'string' && value.endsWith('}}'))
      ) {
        _payload[key] = new CfnJson(this, `ResolveToken-${key}`, {
          value,
        }).value;
      } else if (typeof value === 'object') {
        _payload[key] = this.resolveTokens(value);
      } else if (Array.isArray(value)) {
        _payload[key] = value.map((v) => this.resolveTokens(v));
      } else {
        _payload[key] = value;
      }
    });
    return _payload;
  };
}

export class CloudfrontWebAcl extends Stack {
  public readonly wafArn;
  constructor(scope: Construct, id: string) {
    super(scope, id, {
      env: {
        region: 'us-east-1',
        account: Stack.of(scope).account,
      },
      crossRegionReferences: true,
    });

    this.wafArn = new CfnWebACL(this, 'WebAcl', {
      defaultAction: { allow: {} },
      scope: 'CLOUDFRONT',
      visibilityConfig: {
        cloudWatchMetricsEnabled: true,
        metricName: id,
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
    }).attrArn;
  }
}
