/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import type { CodegenConfig } from '@graphql-codegen/cli';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const config: CodegenConfig = {
  schema: [path.join(__dirname, 'src/schema/*.graphql')],
  documents: [path.join(__dirname, 'src/documents/**/*.graphql')],
  overwrite: true,
  emitLegacyCommonJSImports: false,
  generates: {
    [path.join(__dirname, 'src/graphql/')]: {
      preset: 'client',
      config: {
        documentMode: 'documentNode',
        importOperationTypesFrom: 'Types',
        enumsAsTypes: true,
        dedupeFragments: true,
      },
    },
  },
};

export default config;
