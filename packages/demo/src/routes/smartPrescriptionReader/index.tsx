/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { createFileRoute } from '@tanstack/react-router';
import SmartPrescriptionReader from '../../pages/SmartPrescriptionReader';

export const Route = createFileRoute('/smartPrescriptionReader/')({
  component: RouteComponent,
});

function RouteComponent() {
  return <SmartPrescriptionReader />;
}
