/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

export interface ICognitoProps {
  region: string;
  identityPoolId: string;
  userPoolId: string;
  userPoolWebClientId: string;
}

export interface IRuntimeConfig {
  cognitoProps: ICognitoProps;
  graphqlEndpoint: string;
  inputBucket: string;
}
