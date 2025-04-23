/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { createRootRoute } from '@tanstack/react-router';
import AppLayout from '../components/AppLayout';

export const Route = createRootRoute({
  component: () => <AppLayout />,
});
