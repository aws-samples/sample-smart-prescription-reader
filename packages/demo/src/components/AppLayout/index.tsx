/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { useAuth } from 'react-oidc-context';
import * as React from 'react';
import { createContext, useCallback, useEffect, useState } from 'react';
import { NavItems } from './navitems';
import Config from '../../config';

import {
  BreadcrumbGroup,
  BreadcrumbGroupProps,
  Flashbar,
  SideNavigation,
  TopNavigation,
} from '@cloudscape-design/components';
import CloudscapeAppLayout, {
  AppLayoutProps,
} from '@cloudscape-design/components/app-layout';
import { matchByPath, useLocation, useNavigate } from '@tanstack/react-router';
import { Outlet } from '@tanstack/react-router';
import { useGlobalUIContext } from '../../hooks/useGlobalUIContext';
import helpPanelContent from '../../help/helpPanelContent';

const getBreadcrumbs = (
  pathName: string,
  search: string,
  defaultBreadcrumb: string,
  availableRoutes?: string[],
) => {
  const segments = [
    defaultBreadcrumb,
    ...pathName.split('/').filter((segment) => segment !== ''),
  ];

  return segments.map((segment, i) => {
    const href =
      i === 0
        ? '/'
        : `/${segments
            .slice(1, i + 1)
            .join('/')
            .replace('//', '/')}`;

    const matched =
      !availableRoutes || availableRoutes.find((r) => matchByPath(r, href, {}));

    return {
      href: matched ? `${href}${search}` : '#',
      text: segment,
    };
  });
};

export interface AppLayoutContext {
  appLayoutProps: AppLayoutProps;
  setAppLayoutProps: (props: AppLayoutProps) => void;
  displayHelpPanel: (helpContent: React.ReactNode) => void;
}

/**
 * Context for updating/retrieving the AppLayout.
 */
export const AppLayoutContext = createContext({
  appLayoutProps: {},

  setAppLayoutProps: (_: AppLayoutProps) => {},

  displayHelpPanel: (_: React.ReactNode) => {},
});

/**
 * Defines the App layout and contains logic for routing.
 */
const AppLayout: React.FC = () => {
  const { user, removeUser, signoutRedirect, clearStaleState } = useAuth();
  const navigate = useNavigate();
  const [activeBreadcrumbs, setActiveBreadcrumbs] = useState<
    BreadcrumbGroupProps.Item[]
  >([{ text: '/', href: '/' }]);
  const [appLayoutProps, setAppLayoutProps] = useState<AppLayoutProps>({});
  const { pathname, search } = useLocation();
  const setAppLayoutPropsSafe = useCallback(
    (props: AppLayoutProps) => {
      JSON.stringify(appLayoutProps) !== JSON.stringify(props) &&
        setAppLayoutProps(props);
    },
    [appLayoutProps],
  );
  const { flashItems, toolsOpen, setToolsOpen, helpPanelTopic, appLayoutRef } =
    useGlobalUIContext();
  useEffect(() => {
    const breadcrumbs = getBreadcrumbs(
      pathname,
      Object.entries(search).reduce((p, [k, v]) => p + `${k}=${v}`, ''),
      '/',
    );
    setActiveBreadcrumbs(breadcrumbs);
  }, [pathname, search]);
  const onNavigate = useCallback(
    (
      e: CustomEvent<{
        href: string;
        external?: boolean;
      }>,
    ) => {
      if (!e.detail.external) {
        e.preventDefault();
        setAppLayoutPropsSafe({
          contentType: undefined,
        });
        navigate({ to: e.detail.href });
      }
    },
    [navigate, setAppLayoutPropsSafe],
  );
  return (
    <AppLayoutContext.Provider
      value={{
        appLayoutProps,
        setAppLayoutProps: setAppLayoutPropsSafe,
        displayHelpPanel: (helpContent: React.ReactNode) => {
          setAppLayoutPropsSafe({ tools: helpContent, toolsHide: false });
          appLayoutRef.current?.openTools();
        },
      }}
    >
      <TopNavigation
        identity={{
          href: '/',
          title: Config.applicationName,
          logo: {
            src: Config.logo,
          },
        }}
        utilities={[
          {
            type: 'menu-dropdown',
            text: `${user?.profile?.['cognito:username']}`,
            iconName: 'user-profile-active',
            onItemClick: (e) => {
              if (e.detail.id === 'signout') {
                removeUser();
                signoutRedirect({
                  post_logout_redirect_uri: window.location.origin,
                  extraQueryParams: {
                    redirect_uri: window.location.origin,
                    response_type: 'code',
                  },
                });
                clearStaleState();
              }
            },
            items: [{ id: 'signout', text: 'Sign out' }],
          },
        ]}
      />
      <CloudscapeAppLayout
        ref={appLayoutRef}
        breadcrumbs={
          <BreadcrumbGroup onFollow={onNavigate} items={activeBreadcrumbs} />
        }
        toolsOpen={toolsOpen}
        onToolsChange={(event) => setToolsOpen(event.detail.open)}
        tools={helpPanelContent[helpPanelTopic]}
        navigation={
          <SideNavigation
            header={{ text: Config.applicationName, href: '/' }}
            activeHref={pathname}
            onFollow={onNavigate}
            items={NavItems}
          />
        }
        content={<Outlet />}
        notifications={<Flashbar items={flashItems} />}
        {...appLayoutProps}
      />
    </AppLayoutContext.Provider>
  );
};

export default AppLayout;
