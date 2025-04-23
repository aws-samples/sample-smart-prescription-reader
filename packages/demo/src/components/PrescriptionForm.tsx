/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import {
  Button,
  Container,
  Form,
  FormField,
  Header,
  Input,
  SpaceBetween,
} from '@cloudscape-design/components';
import { JSONSchemaType } from 'ajv';
import { useState } from 'react';

const DynamicFormField: React.FC<{
  property: JSONSchemaType<any>;
  path: string;
  value: any;
  onChange: (path: string, value: any) => void;
}> = ({ property, path, value, onChange }) => {
  if (property.type === 'object' && property.properties) {
    return (
      <SpaceBetween size="m">
        {Object.entries(property.properties as JSONSchemaType<any>).map(
          ([key, prop]) => {
            if (prop.type === 'array' && prop.items) {
              return (
                <Container
                  header={
                    <Header
                      variant="h3"
                      actions={
                        <Button
                          onClick={() => {
                            onChange(`${path}.${key}`, [
                              ...(value[key] || []),
                              {},
                            ]);
                          }}
                        >
                          Add Item
                        </Button>
                      }
                    >
                      {key.slice(0, 1).toUpperCase() + key.slice(1)}
                    </Header>
                  }
                >
                  <DynamicFormField
                    property={prop}
                    path={`${path}.${key}`}
                    value={value?.[key]}
                    onChange={onChange}
                  />
                </Container>
              );
            } else {
              return (
                <FormField
                  key={key}
                  label={key.slice(0, 1).toUpperCase() + key.slice(1)}
                  description={prop.description}
                >
                  <DynamicFormField
                    property={prop}
                    path={`${path}.${key}`}
                    value={value?.[key]}
                    onChange={onChange}
                  />
                </FormField>
              );
            }
          },
        )}
      </SpaceBetween>
    );
  }

  if (property.type === 'array' && property.items) {
    return (
      <SpaceBetween size="m">
        {(value || []).map((_: any, index: number) => (
          <SpaceBetween size="m">
            <DynamicFormField
              property={property.items!}
              path={`${path}[${index}]`}
              value={value[index]}
              onChange={onChange}
            />
            <Button
              onClick={() => {
                const newValue = [...value];
                newValue.splice(index, 1);
                onChange(path, newValue);
              }}
            >
              Remove
            </Button>
          </SpaceBetween>
        ))}
      </SpaceBetween>
    );
  }

  return (
    <Input
      value={value || ''}
      onChange={(event) => onChange(path, event.detail.value)}
    />
  );
};

export interface PrescriptionFormProps {
  data: object | object[] | undefined;
  schema: string;
}

const PrescriptionForm = (props: PrescriptionFormProps) => {
  const [formData, setFormData] = useState(props.data);

  const handleChange = (path: string, value: any) => {
    const updateNestedValue = (obj: any, pathArray: string[], v: any): any => {
      // If we're at the end of the path, return the new value
      if (pathArray.length === 0) {
        return v;
      }

      const [current, ...rest] = pathArray;

      // Handle array updates
      const match = current.match(/([a-zA-Z0-9]+)\[(\d+)\]/);
      if (match) {
        // Handle array updates
        const key = match[1];
        const index = parseInt(match[2]);
        const newArray = Array.isArray(obj[key]) ? [...obj[key]] : [];
        newArray[index] = updateNestedValue(newArray[index], rest, v);
        return { ...obj, [key]: newArray };
      }

      // Handle object updates
      return {
        ...obj,
        [current]: updateNestedValue(obj?.[current], rest, v),
      };
    };

    // Remove empty strings from path array but keep the structure
    const pathArray = path.split('.').filter(Boolean);
    const newData = updateNestedValue(formData, pathArray, value);
    setFormData(newData);
  };

  return (
    <Container header={<h3>Prescription Data</h3>} fitHeight={true}>
      <Form>
        <DynamicFormField
          property={JSON.parse(props.schema)}
          path=""
          value={formData}
          onChange={handleChange}
        />
      </Form>
    </Container>
  );
};
export default PrescriptionForm;
