/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { useContext, useMemo } from 'react';
import { GlobalUIContext } from '../components/GlobalUIContextProvider';

export const useGlobalUIContext = () => {
  const globalUIContext = useContext(GlobalUIContext);
  return useMemo(() => {
    return globalUIContext;
  }, [globalUIContext]);
};
