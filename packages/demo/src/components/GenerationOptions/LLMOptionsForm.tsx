/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import {
  Checkbox,
  Input,
  Select,
  SelectProps,
  Slider,
  SpaceBetween,
} from '@cloudscape-design/components';
import FormField from '@cloudscape-design/components/form-field';
import { useState } from 'react';
import {
  defaultFastModel,
  defaultJudgeModel,
  defaultPowerfulModel,
  defaultTemperature,
} from '../../hooks/usePrescriptionExtraction';

export const BedrockModels: SelectProps.Option[] = [
  {
    label: 'Anthropic Claude 3 Haiku (Cross Region)',
    value: 'us.anthropic.claude-3-haiku-20240307-v1:0',
  },
  {
    label: 'Anthropic Claude 3 Haiku',
    value: 'anthropic.claude-3-haiku-20240307-v1:0',
  },
  {
    label: 'Anthropic Claude 3 Sonnet (Cross Region)',
    value: 'us.anthropic.claude-3-sonnet-20240229-v1:0',
  },
  {
    label: 'Anthropic Claude 3 Sonnet',
    value: 'anthropic.claude-3-sonnet-20240229-v1:0',
  },
  {
    label: 'Anthropic Claude 3.5 Sonnet (Cross Region)',
    value: 'us.anthropic.claude-3-5-sonnet-20240620-v1:0',
  },
  {
    label: 'Anthropic Claude 3.5 Sonnet',
    value: 'anthropic.claude-3-5-sonnet-20240620-v1:0',
  },
  {
    label: 'Anthropic Claude 3.5 Sonnet V2 (2024-10-22) (Cross Region)',
    value: 'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
  },
  {
    label: 'Anthropic Claude 3.5 Sonnet V2 (2024-10-22)',
    value: 'anthropic.claude-3-5-sonnet-20241022-v2:0',
  },
  {
    label: 'Anthropic Claude 3.7 Sonnet (Cross Region)',
    value: 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
  },
  {
    label: 'Anthropic Claude 3.7 Sonnet',
    value: 'anthropic.claude-3-7-sonnet-20250219-v1:0',
  },
  {
    label: 'Amazon Nova Lite (Cross Region)',
    value: 'us.amazon.nova-lite-v1:0',
  },
  {
    label: 'Amazon Nova Lite',
    value: 'amazon.nova-lite-v1:0',
  },
  {
    label: 'Amazon Nova Pro (Cross Region)',
    value: 'us.amazon.nova-pro-v1:0',
  },
  {
    label: 'Amazon Nova Pro',
    value: 'amazon.nova-pro-v1:0',
  },
];

export interface LLMOptionsFormProps {
  ocr: boolean;
  setOcr: React.Dispatch<React.SetStateAction<boolean>>;
  correctionIterations: number;
  setCorrectionIterations: React.Dispatch<React.SetStateAction<number>>;
  temperature: number;
  setTemperature: React.Dispatch<React.SetStateAction<number>>;
  fastModel: string;
  setFastModel: React.Dispatch<React.SetStateAction<string>>;
  judgeModel: string;
  setJudgeModel: React.Dispatch<React.SetStateAction<string>>;
  powerfulModel: string;
  setPowerfulModel: React.Dispatch<React.SetStateAction<string>>;
}

const LLMOptionsForm: React.FC<LLMOptionsFormProps> = (
  props: LLMOptionsFormProps,
) => {
  const {
    ocr,
    setOcr,
    temperature,
    setTemperature,
    fastModel,
    setFastModel,
    judgeModel,
    setJudgeModel,
    powerfulModel,
    setPowerfulModel,
    correctionIterations,
    setCorrectionIterations,
  } = props;
  const [temperatureError, setTemperatureError] = useState<
    string | undefined
  >();
  const [correctionIterationsError, setCorrectionIterationsError] = useState<
    string | undefined
  >();

  return (
    <SpaceBetween direction="vertical" size="l">
      <FormField label="OCR" description="Enable OCR with Textract">
        <Checkbox
          checked={ocr}
          onChange={({ detail }) => {
            setOcr(detail.checked);
          }}
        >
          Enable OCR
        </Checkbox>
      </FormField>
      <FormField label="Fast Model" description="Choose a fast model">
        <Select
          selectedOption={
            fastModel === ''
              ? null
              : BedrockModels.filter((m) => m.value === fastModel)[0]
          }
          placeholder={
            BedrockModels.filter((m) => m.value === defaultFastModel)[0].label
          }
          options={BedrockModels}
          onChange={({ detail }) => {
            setFastModel(
              detail.selectedOption.value ? detail.selectedOption.value : '',
            );
          }}
        ></Select>
      </FormField>
      <FormField label="Judge Model" description="Choose a judge model">
        <Select
          selectedOption={
            judgeModel === ''
              ? null
              : BedrockModels.filter((m) => m.value === judgeModel)[0]
          }
          placeholder={
            BedrockModels.filter((m) => m.value === defaultJudgeModel)[0].label
          }
          options={BedrockModels}
          onChange={({ detail }) => {
            setJudgeModel(
              detail.selectedOption.value ? detail.selectedOption.value : '',
            );
          }}
        ></Select>
      </FormField>
      <FormField label="Powerful Model" description="Choose a powerful model">
        <Select
          selectedOption={
            powerfulModel === ''
              ? null
              : BedrockModels.filter((m) => m.value === powerfulModel)[0]
          }
          placeholder={
            BedrockModels.filter((m) => m.value === defaultPowerfulModel)[0]
              .label
          }
          options={BedrockModels}
          onChange={({ detail }) => {
            setPowerfulModel(
              detail.selectedOption.value ? detail.selectedOption.value : '',
            );
          }}
        ></Select>
      </FormField>
      <FormField
        label="Correction Iterations"
        description="Maximum iterations to correct the prescription"
        errorText={correctionIterationsError}
      >
        <div className="llmoptions-input-wrapper">
          <Input
            value={correctionIterations.toString()}
            type="number"
            inputMode="numeric"
            onChange={({ detail }) => {
              const value = Number(detail.value);
              if (isNaN(value)) {
                setCorrectionIterationsError(
                  'Correction iterations must be a number',
                );
              } else if (!Number.isInteger(value)) {
                setCorrectionIterationsError(
                  'Correction iterations must be an integer',
                );
              } else if (value < 0 || value > 5) {
                setCorrectionIterationsError(
                  'Correction iterations must be between 0 and 5',
                );
              } else {
                setCorrectionIterationsError(undefined);
              }
              setCorrectionIterations(value);
            }}
          />
        </div>
      </FormField>
      <FormField
        label="Temperature"
        description="Adjust the likelihood of randomness"
        errorText={temperatureError}
      >
        <div className="llmoptions-flex-wrapper">
          <div className="llmoptions-slider-wrapper">
            <Slider
              onChange={({ detail }) => {
                setTemperatureError(undefined);
                setTemperature(detail.value);
              }}
              value={temperature}
              valueFormatter={(value) => value.toFixed(1)}
              step={0.1}
              max={1}
              min={0}
            />
          </div>
          <SpaceBetween size="m" alignItems="center" direction="horizontal">
            <div className="llmoptions-input-wrapper">
              <Input
                value={temperature.toFixed(1)}
                step={0.1}
                onChange={({ detail }) => {
                  const value = Number(detail.value);
                  if (isNaN(value)) {
                    setTemperatureError('Temperature must be a number');
                  } else if (value < 0 || value > 1) {
                    setTemperatureError('Temperature must be between 0 and 1');
                  } else {
                    setTemperatureError(undefined);
                  }
                  setTemperature(value);
                }}
                placeholder={defaultTemperature.toFixed(1)}
                type="number"
                inputMode="numeric"
                controlId="validation-input"
              />
            </div>
          </SpaceBetween>
        </div>
      </FormField>
    </SpaceBetween>
  );
};

export default LLMOptionsForm;
