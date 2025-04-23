/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { useContext } from 'react';
import { RuntimeConfigContext } from '../components/RuntimeConfig';
import { IRuntimeConfig } from ':smart-prescription-reader/common-types';

export const useRuntimeConfig = (): IRuntimeConfig => {
  const runtimeConfig = useContext(RuntimeConfigContext);

  if (!runtimeConfig) {
    throw new Error(
      'useRuntimeConfig must be used within a RuntimeConfigProvider',
    );
  }

  return runtimeConfig;
};
