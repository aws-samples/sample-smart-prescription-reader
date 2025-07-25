/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import React, { PropsWithChildren, useEffect } from 'react';
import { AuthProvider, AuthProviderProps, useAuth } from 'react-oidc-context';
import { Alert, Spinner } from '@cloudscape-design/components';
import { useRuntimeConfig } from '../../hooks/useRuntimeConfig';

/**
 * Sets up the Cognito auth.
 *
 * This assumes a runtime-config.json file is present at '/'. In order for Auth to be set up automatically,
 * the runtime-config.json must have the cognitoProps set.
 */
const CognitoAuth: React.FC<PropsWithChildren> = ({ children }) => {
  const { cognitoProps } = useRuntimeConfig();

  if (!cognitoProps) {
    return (
      <Alert type="error" header="Runtime config configuration error">
        The cognitoProps have not been configured in the runtime-config.json.
      </Alert>
    );
  }

  const cognitoAuthConfig: AuthProviderProps = {
    authority: `https://cognito-idp.${cognitoProps.region}.amazonaws.com/${cognitoProps.userPoolId}`,
    client_id: cognitoProps.userPoolWebClientId,
    redirect_uri: window.location.origin,
    response_type: 'code',
    scope: 'email openid profile',
  };

  return (
    <AuthProvider {...cognitoAuthConfig}>
      <CognitoAuthInternal>{children}</CognitoAuthInternal>
    </AuthProvider>
  );
};

const CognitoAuthInternal: React.FC<PropsWithChildren> = ({ children }) => {
  const auth = useAuth();

  useEffect(() => {
    if (!auth.isAuthenticated && !auth.isLoading) {
      auth.signinRedirect();
    }
  }, [auth]);

  if (auth.isAuthenticated) {
    return children;
  } else if (auth.error) {
    return (
      <Alert type="error" header="Configuration error">
        Error contacting Cognito. Please check your runtime-config.json is
        configured with the correct endpoints.
      </Alert>
    );
  } else {
    return <Spinner />;
  }
};

export default CognitoAuth;
