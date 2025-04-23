/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import * as url from 'url';
import { Construct } from 'constructs';
import { StaticWebsite } from '../../core/index.js';

export class Demo extends StaticWebsite {
  constructor(scope: Construct, id: string) {
    super(scope, id, {
      websiteFilePath: url.fileURLToPath(
        new URL('../../../../../../dist/packages/demo/bundle', import.meta.url),
      ),
    });
  }
}
