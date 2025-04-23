/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import type { IRuntimeConfig } from ':smart-prescription-reader/common-types';
import { Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';

const RuntimeConfigKey = '__RuntimeConfig__';

export class RuntimeConfig extends Construct {
  private readonly _runtimeConfig: Partial<IRuntimeConfig> = {};

  static ensure(scope: Construct): RuntimeConfig {
    const stack = Stack.of(scope);
    return (
      RuntimeConfig.of(scope) ?? new RuntimeConfig(stack, RuntimeConfigKey)
    );
  }

  static of(scope: Construct): RuntimeConfig | undefined {
    const stack = Stack.of(scope);
    return stack.node.tryFindChild(RuntimeConfigKey) as
      | RuntimeConfig
      | undefined;
  }

  constructor(scope: Construct, id: string) {
    super(scope, id);
  }

  get config(): Partial<IRuntimeConfig> {
    return this._runtimeConfig;
  }
}
