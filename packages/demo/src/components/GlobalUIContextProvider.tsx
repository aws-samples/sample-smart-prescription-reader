/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import { FlashbarProps } from '@cloudscape-design/components';
import { AppLayoutProps } from '@cloudscape-design/components/app-layout';
import * as React from 'react';
import { useCallback, useRef, useState } from 'react';

export interface GlobalUIContextType {
  flashItems: FlashbarProps.MessageDefinition[];
  setFlashItems: React.Dispatch<
    React.SetStateAction<FlashbarProps.MessageDefinition[]>
  >;
  addFlashItem: (item: FlashbarProps.MessageDefinition) => void;
  toolsOpen: boolean;
  setToolsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  helpPanelTopic: string;
  setHelpPanelTopic: React.Dispatch<React.SetStateAction<string>>;
  makeHelpPanelHandler: (topic: string) => void;
  appLayoutRef: React.RefObject<any>;
}

export const GlobalUIContext = React.createContext<GlobalUIContextType>({
  flashItems: [],
  setFlashItems: () => {},
  addFlashItem: () => {},
  toolsOpen: false,
  setToolsOpen: () => {},
  helpPanelTopic: 'default',
  setHelpPanelTopic: () => {},
  makeHelpPanelHandler: () => {},
  appLayoutRef: {} as React.RefObject<any>,
});

const GlobalUIContextProvider: React.FC<any> = ({ children }) => {
  const [flashItems, setFlashItems] = useState<
    FlashbarProps.MessageDefinition[]
  >([]);

  const addFlashItem = (item: FlashbarProps.MessageDefinition) => {
    const id = new Date().getTime().toString();
    item.id = id;
    item.dismissible = true;
    item.onDismiss = () =>
      setFlashItems((prev) => prev.filter((f) => f.id !== id));
    setFlashItems((prev) => [...prev, item]);
  };

  const [toolsOpen, setToolsOpen] = useState(false);
  const [helpPanelTopic, setHelpPanelTopic] = useState('default');
  const appLayoutRef = useRef<AppLayoutProps.Ref>(null);

  const makeHelpPanelHandler = useCallback(
    (topic: string) => {
      setHelpPanelTopic(topic);
      setToolsOpen(true);
      appLayoutRef.current?.focusToolsClose();
    },
    [appLayoutRef],
  );

  const setHelpPanelTopicIfDefault: React.Dispatch<
    React.SetStateAction<string>
  > = (topic) => {
    if (helpPanelTopic === 'default') {
      setHelpPanelTopic(topic);
    }
  };

  return (
    <GlobalUIContext.Provider
      value={{
        flashItems,
        setFlashItems,
        addFlashItem,
        toolsOpen,
        setToolsOpen,
        helpPanelTopic,
        setHelpPanelTopic: setHelpPanelTopicIfDefault,
        makeHelpPanelHandler,
        appLayoutRef,
      }}
    >
      {children}
    </GlobalUIContext.Provider>
  );
};

export default GlobalUIContextProvider;
