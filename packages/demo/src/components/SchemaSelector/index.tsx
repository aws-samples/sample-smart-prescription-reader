/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import {
  CodeEditor,
  CodeEditorProps,
  ExpandableSection,
  FormField,
  Input,
  NonCancelableCustomEvent,
  Select,
} from '@cloudscape-design/components';
import Ajv from 'ajv';
import { useCallback, useEffect, useMemo, useState } from 'react';
// @ts-expect-error Cannot find module
import { OptionDefinition } from '@cloudscape-design/components/internal/components/option/interfaces';
import { defaultSchemaName, defaultSchemas } from './defaultSchemas';

export interface SchemaSelectorProps {
  schema: string;
  setSchema: React.Dispatch<React.SetStateAction<string>>;
}

interface BaseChangeDetail {
  value: string;
}

const ajv = new Ajv();

const aceLoader = async () => import('ace-builds');

const Index = ({ schema, setSchema }: SchemaSelectorProps) => {
  const [error, setError] = useState<string | undefined>();
  const [preferences, setPreferences] =
    useState<Partial<CodeEditorProps.Preferences>>();
  const [loading, setLoading] = useState(true);
  const [ace, setAce] = useState<any>();
  const [schemaName, setSchemaName] = useState('');
  const [currentSchemaName, setCurrentSchemaName] = useState('');
  const [selectedSchemaOption, setSelectedSchemaOption] = useState({
    value: '',
    label: '',
  });
  const [savedSchemas, setSavedSchemas] = useState<{ [key: string]: string }>(
    defaultSchemas,
  );
  const [isEditorVisible, setIsEditorVisible] = useState(false);

  // Memoize schema options
  const schemaOptions = useMemo(
    () => [
      { label: 'Create new schema...', value: 'new' },
      { label: defaultSchemaName, value: defaultSchemaName },
      ...Object.keys(savedSchemas)
        .filter((name) => name !== defaultSchemaName)
        .map((name) => ({
          label: name,
          value: name,
        })),
    ],
    [savedSchemas],
  );

  // Load ace editor
  useEffect(() => {
    let mounted = true;
    aceLoader()
      .then((aceModule) => {
        if (mounted) {
          setAce(aceModule);
          setLoading(false);
        }
      })
      .catch(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  // Load saved schemas
  useEffect(() => {
    const storedSchemas = localStorage.getItem('savedSchemas');
    const storedLastSchema = localStorage.getItem('lastSchema');

    if (storedSchemas) {
      const schemas = JSON.parse(storedSchemas);
      setSavedSchemas(schemas);

      const lastSchema = storedLastSchema || defaultSchemaName;
      setSelectedSchemaOption({
        value: lastSchema,
        label: lastSchema,
      });
      setSchema(schemas[lastSchema]);
      setCurrentSchemaName(lastSchema);
      setSchemaName(lastSchema);
    } else {
      localStorage.setItem('savedSchemas', JSON.stringify(defaultSchemas));
      localStorage.setItem('lastSchema', defaultSchemaName);
      setSelectedSchemaOption({
        value: defaultSchemaName,
        label: defaultSchemaName,
      });
      setSchema(defaultSchemas[defaultSchemaName]);
    }
  }, [setSchema]);

  // Memoize handlers
  const handleSchemaSelect = useCallback(
    (option: OptionDefinition) => {
      setSelectedSchemaOption(option);
      if (option.value === 'new') {
        setSchema('');
        setSchemaName('');
        setCurrentSchemaName('');
        setIsEditorVisible(true);
      } else {
        setSchema(savedSchemas[option.value]);
        setCurrentSchemaName(option.value);
        setSchemaName(option.value);
        localStorage.setItem('lastSchema', option.value);
      }
    },
    [savedSchemas, setSchema],
  );

  const handleSchemaChange = useCallback(
    async (event: NonCancelableCustomEvent<BaseChangeDetail>) => {
      const newSchema = event.detail.value;
      setSchema(newSchema);

      try {
        await ajv.validateSchema(JSON.parse(newSchema), true);
        setError(undefined);

        if (schemaName) {
          const updatedSchemas = {
            ...Object.fromEntries(
              Object.entries(savedSchemas).filter(
                ([key]) => key !== currentSchemaName,
              ),
            ),
            [schemaName]: newSchema,
          };
          setSavedSchemas(updatedSchemas);
          localStorage.setItem('savedSchemas', JSON.stringify(updatedSchemas));
          localStorage.setItem('lastSchema', schemaName);
        }
      } catch (e) {
        setError(
          `Invalid JSON Schema: ${(e as Error).message.replace('strict mode: ', '')}`,
        );
      }
    },
    [schemaName, currentSchemaName, savedSchemas, setSchema],
  );

  return (
    <FormField
      label="Prescription Attributes"
      description="What fields do you want to extract from the prescription image?"
    >
      <Select
        selectedOption={selectedSchemaOption}
        onChange={(event) => handleSchemaSelect(event.detail.selectedOption)}
        options={schemaOptions}
        placeholder="Select a schema"
      />
      <ExpandableSection
        variant="inline"
        headerText="Schema Editor"
        expanded={isEditorVisible}
        onChange={({ detail }) => setIsEditorVisible(detail.expanded)}
      >
        <FormField label="Schema Name">
          <Input
            value={schemaName}
            onChange={(event) => {
              const newName = event.detail.value;
              if (schema) {
                const updatedSchemas = {
                  ...Object.fromEntries(
                    Object.entries(savedSchemas).filter(
                      ([key]) => key !== schemaName,
                    ),
                  ),
                  [newName]: schema,
                };
                setSavedSchemas(updatedSchemas);
                localStorage.setItem(
                  'savedSchemas',
                  JSON.stringify(updatedSchemas),
                );
                localStorage.setItem('lastSchema', newName);
                setSelectedSchemaOption({ value: newName, label: newName });
              }
              setSchemaName(newName);
            }}
          />
        </FormField>
        <FormField errorText={error}>
          <CodeEditor
            ace={ace}
            loading={loading}
            language={'json'}
            value={schema}
            onDelayedChange={handleSchemaChange}
            preferences={preferences}
            onPreferencesChange={(e) => setPreferences(e.detail)}
          />
        </FormField>
      </ExpandableSection>{' '}
    </FormField>
  );
};

export default Index;
