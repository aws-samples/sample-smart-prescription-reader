/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { useRuntimeConfig } from './useRuntimeConfig';
import { useAuth } from 'react-oidc-context';
import { useMemo } from 'react';
import request, { RequestDocument } from 'graphql-request';
import { TypedDocumentNode } from '@graphql-typed-document-node/core';

interface GraphQLVariables {
  [key: string]: never;
}

export const useGraphqlClient = () => {
  const { graphqlEndpoint } = useRuntimeConfig();
  const { user } = useAuth();
  return useMemo(() => {
    return async <
      TData = unknown,
      TVariables extends object = GraphQLVariables,
    >(
      document: RequestDocument | TypedDocumentNode<TData, TVariables>,
      variables: TVariables,
    ): Promise<TData> => {
      return request<TData>(graphqlEndpoint, document, variables, {
        Authorization: user?.access_token ? `${user.access_token}` : '',
      });
    };
  }, [graphqlEndpoint, user?.access_token]);
};
