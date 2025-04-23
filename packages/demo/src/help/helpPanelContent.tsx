/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { HelpPanel } from '@cloudscape-design/components';
import { ReactNode } from 'react';

type HelpPanelContent = {
  [key: string]: ReactNode;
};

const helpPanelContent: HelpPanelContent = {
  default: (
    <HelpPanel>
      <div>
        <p>There is no additional help content on this page.</p>
      </div>
    </HelpPanel>
  ),
};

export default helpPanelContent;
