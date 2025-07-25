/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import * as crypto from 'crypto';
import {
  IdentityPool,
  UserPoolAuthenticationProvider,
} from 'aws-cdk-lib/aws-cognito-identitypool';
import { CfnOutput, Duration, Lazy, Stack } from 'aws-cdk-lib';
import {
  AccountRecovery,
  CfnManagedLoginBranding,
  CfnUserPoolDomain,
  FeaturePlan,
  Mfa,
  OAuthScope,
  UserPool,
  UserPoolClient,
} from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';
import { RuntimeConfig } from './runtime-config.js';
import { Distribution } from 'aws-cdk-lib/aws-cloudfront';

const WEB_CLIENT_ID = 'WebClient';

/**
 * Creates a UserPool and Identity Pool with sane defaults configured intended for usage from a web client.
 */
export class UserIdentity extends Construct {
  public readonly region: string;
  public readonly identityPool: IdentityPool;
  public readonly userPool: UserPool;
  public readonly userPoolClient: UserPoolClient;
  public readonly userPoolDomain: CfnUserPoolDomain;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.region = Stack.of(this).region;
    this.userPool = this.createUserPool();
    this.userPoolDomain = this.createUserPoolDomain(this.userPool);
    this.userPoolClient = this.createUserPoolClient(this.userPool);
    this.identityPool = this.createIdentityPool(
      this.userPool,
      this.userPoolClient,
    );
    this.createManagedLoginBranding(
      this.userPool,
      this.userPoolClient,
      this.userPoolDomain,
    );

    RuntimeConfig.ensure(this).config.cognitoProps = {
      region: Stack.of(this).region,
      identityPoolId: this.identityPool.identityPoolId,
      userPoolId: this.userPool.userPoolId,
      userPoolWebClientId: this.userPoolClient.userPoolClientId,
    };

    new CfnOutput(this, `${id}-UserPoolId`, {
      value: this.userPool.userPoolId,
    });

    new CfnOutput(this, `${id}-IdentityPoolId`, {
      value: this.identityPool.identityPoolId,
    });
  }

  private createUserPool = () =>
    // amazonq-ignore-next-line
    new UserPool(this, 'UserPool', {
      deletionProtection: true,
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
        tempPasswordValidity: Duration.days(3),
      },
      mfa: Mfa.OPTIONAL,
      featurePlan: FeaturePlan.PLUS,
      mfaSecondFactor: { sms: true, otp: true },
      signInCaseSensitive: false,
      signInAliases: { username: true, email: true },
      accountRecovery: AccountRecovery.EMAIL_ONLY,
      selfSignUpEnabled: false,
      standardAttributes: {
        phoneNumber: { required: false },
        email: { required: true },
        givenName: { required: false },
        familyName: { required: false },
      },
      autoVerify: {
        email: true,
        phone: true,
      },
      keepOriginal: {
        email: true,
        phone: true,
      },
    });

  private createUserPoolDomain = (userPool: UserPool) => {
    const accountId = Stack.of(this).account;
    const region = Stack.of(this).region;
    const stackName = Stack.of(this).stackName.toLowerCase();

    // Crear hash determinístico del account ID + región
    const hash = crypto
      .createHash('sha256')
      .update(`${accountId}-${region}`)
      .digest('hex')
      .substring(0, 8);

    const domainPrefix = `${stackName}-${hash}`;

    // Validar que no exceda el límite de 63 caracteres
    if (domainPrefix.length > 63) {
      throw new Error(
        `Generated domain name '${domainPrefix}' exceeds 63 character limit (${domainPrefix.length} chars). ` +
          `Consider shortening the stack name.`,
      );
    }

    return new CfnUserPoolDomain(this, 'UserPoolDomain', {
      domain: domainPrefix,
      userPoolId: userPool.userPoolId,
      managedLoginVersion: 2,
    });
  };
  private createUserPoolClient = (userPool: UserPool) => {
    const lazilyComputedCallbackUrls = Lazy.list({
      produce: () =>
        [
          'http://localhost:4200',
          `https://${Stack.of(this).region}.console.aws.amazon.com`,
        ].concat(
          this.findCloudFrontDistributions().map(
            (d) => `https://${d.domainName}`,
          ),
        ),
    });

    return userPool.addClient(WEB_CLIENT_ID, {
      authFlows: {
        userPassword: true,
        userSrp: true,
        user: true,
      },
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
        },
        scopes: [OAuthScope.EMAIL, OAuthScope.OPENID, OAuthScope.PROFILE],
        callbackUrls: lazilyComputedCallbackUrls,
        logoutUrls: lazilyComputedCallbackUrls,
      },
      preventUserExistenceErrors: true,
    });
  };

  private createIdentityPool = (
    userPool: UserPool,
    userPoolClient: UserPoolClient,
  ) => {
    const identityPool = new IdentityPool(this, 'IdentityPool');

    identityPool.addUserPoolAuthentication(
      new UserPoolAuthenticationProvider({
        userPool,
        userPoolClient,
      }),
    );

    return identityPool;
  };

  private createManagedLoginBranding = (
    userPool: UserPool,
    userPoolClient: UserPoolClient,
    userPoolDomain: CfnUserPoolDomain,
  ) => {
    new CfnManagedLoginBranding(this, 'ManagedLoginBranding', {
      userPoolId: userPool.userPoolId,
      clientId: userPoolClient.userPoolClientId,
      useCognitoProvidedValues: true,
    }).node.addDependency(userPoolClient, userPool, userPoolDomain);
  };

  private findCloudFrontDistributions = (): Distribution[] =>
    Stack.of(this)
      .node.findAll()
      .filter((child) => child instanceof Distribution);
}
