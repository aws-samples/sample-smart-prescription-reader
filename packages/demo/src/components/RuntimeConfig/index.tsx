/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { Alert, Spinner } from '@cloudscape-design/components';
import React, {
  createContext,
  PropsWithChildren,
  useEffect,
  useState,
} from 'react';
import type { IRuntimeConfig } from ':smart-prescription-reader/common-types';

/**
 * Context for storing the runtimeConfig.
 */
export const RuntimeConfigContext = createContext<IRuntimeConfig | undefined>(
  undefined,
);

/**
 * Sets up the runtimeConfig.
 *
 * This assumes a runtime-config.json file is present at '/'.
 */
const RuntimeConfigProvider: React.FC<PropsWithChildren> = ({ children }) => {
  const [runtimeConfig, setRuntimeConfig] = useState<
    IRuntimeConfig | undefined
  >();
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    fetch('/runtime-config.json')
      .then((response) => {
        return response.json();
      })
      .then((_runtimeConfig) => {
        setRuntimeConfig(_runtimeConfig as IRuntimeConfig);
      })
      .catch(() => {
        setError('No runtime-config.json detected');
      });
  }, [setRuntimeConfig]);

  return error ? (
    <Alert type="error" header="Validation error">
      {error}
    </Alert>
  ) : runtimeConfig ? (
    <RuntimeConfigContext.Provider value={runtimeConfig}>
      {children}
    </RuntimeConfigContext.Provider>
  ) : (
    <Spinner />
  );
};

export default RuntimeConfigProvider;
