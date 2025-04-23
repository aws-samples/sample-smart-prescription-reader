/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */
import path from 'node:path';
import { workspaceRoot } from '@nx/devkit';
import { aws_lambda as lambda } from 'aws-cdk-lib';

export class SmartPrescriptionReaderCode {
  private static instance: lambda.Code | undefined;

  public static getInstance(): lambda.Code {
    if (!this.instance) {
      this.instance = lambda.Code.fromDockerBuild(
        path.join(workspaceRoot, 'packages/core'),
      );
    }
    return this.instance;
  }
}
