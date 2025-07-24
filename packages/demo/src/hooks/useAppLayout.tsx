/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import { useContext } from 'react';
import { AppLayoutContext } from '../components/AppLayout';

export const useAppLayout = (): AppLayoutContext =>
  useContext(AppLayoutContext);
