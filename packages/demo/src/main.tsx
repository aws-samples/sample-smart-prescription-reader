/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import CognitoAuth from './components/CognitoAuth';
import RuntimeConfigProvider from './components/RuntimeConfig';
import React from 'react';
import { createRoot } from 'react-dom/client';
import { I18nProvider } from '@cloudscape-design/components/i18n';
import messages from '@cloudscape-design/components/i18n/messages/all.en';
import { RouterProvider, createRouter } from '@tanstack/react-router';
import { routeTree } from './routeTree.gen';

import '@cloudscape-design/global-styles/index.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GlobalUIContextProvider from './components/GlobalUIContextProvider';

const queryClient = new QueryClient();
const router = createRouter({ routeTree });

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

const root = document.getElementById('root');
root &&
  createRoot(root).render(
    <React.StrictMode>
      <I18nProvider locale="en" messages={[messages]}>
        <RuntimeConfigProvider>
          <CognitoAuth>
            <QueryClientProvider client={queryClient}>
              <GlobalUIContextProvider>
                <RouterProvider router={router} />
              </GlobalUIContextProvider>
            </QueryClientProvider>
          </CognitoAuth>
        </RuntimeConfigProvider>
      </I18nProvider>
    </React.StrictMode>,
  );
