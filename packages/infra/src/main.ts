/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */
import { PDKNag } from '@aws/pdk/pdk-nag';
import { ApplicationStack } from './stacks/applicationStack.js';
import { AwsSolutionsChecks } from 'cdk-nag';
import { CdkGraph, FilterPreset, Filters } from '@aws/pdk/cdk-graph';
import { CdkGraphDiagramPlugin } from '@aws/pdk/cdk-graph-plugin-diagram';
import { CdkGraphThreatComposerPlugin } from '@aws/pdk/cdk-graph-plugin-threat-composer';

(async () => {
  const app = PDKNag.app({
    nagPacks: [new AwsSolutionsChecks()],
  });

  // Use this to deploy your own sandbox environment (assumes your CLI credentials)
  new ApplicationStack(app, 'SmartPrescriptionReader', {
    description: 'Smart Prescription Reader (uksb-3hduwicyoi)',
    env: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION,
    },
  });

  const graph = new CdkGraph(app, {
    plugins: [
      new CdkGraphDiagramPlugin({
        defaults: {
          filterPlan: {
            preset: FilterPreset.COMPACT,
            filters: [{ store: Filters.pruneCustomResources() }],
          },
        },
      }),
      new CdkGraphThreatComposerPlugin(),
    ],
  });

  app.synth();
  await graph.report();
})();
