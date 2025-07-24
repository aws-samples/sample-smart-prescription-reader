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
  ExpandableSection,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';
import LLMOptionsForm from './GenerationOptions/LLMOptionsForm';
import ImageUploader from './ImageUploader';
import { UseQueryResult } from '@tanstack/react-query';
import { GetJobStatusQuery } from ':smart-prescription-reader/models-graphql';
import SchemaSelector from './SchemaSelector';

export interface NewPrescriptionFormProps {
  imageFiles: File[];
  setImageFiles: React.Dispatch<React.SetStateAction<File[]>>;
  schema: string;
  setSchema: React.Dispatch<React.SetStateAction<string>>;
  fastModel: string;
  setFastModel: React.Dispatch<React.SetStateAction<string>>;
  judgeModel: string;
  setJudgeModel: React.Dispatch<React.SetStateAction<string>>;
  powerfulModel: string;
  setPowerfulModel: React.Dispatch<React.SetStateAction<string>>;
  temperature: number;
  setTemperature: React.Dispatch<React.SetStateAction<number>>;
  extractPrescriptionData: () => Promise<void>;
  status: string;
  extractPrescription: UseQueryResult<GetJobStatusQuery, Error>;
  ocr: boolean;
  setOcr: React.Dispatch<React.SetStateAction<boolean>>;
  correctionIterations: number;
  setCorrectionIterations: React.Dispatch<React.SetStateAction<number>>;
}

const NewPrescriptionForm = (props: NewPrescriptionFormProps) => {
  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Provide prescription images and desired fields to extract"
        >
          Prescription Input
        </Header>
      }
    >
      <SpaceBetween size="l">
        <ImageUploader
          value={props.imageFiles}
          setValue={props.setImageFiles}
        />
        <SchemaSelector schema={props.schema} setSchema={props.setSchema} />
        <ExpandableSection headerText="Options">
          <LLMOptionsForm
            fastModel={props.fastModel}
            setFastModel={props.setFastModel}
            judgeModel={props.judgeModel}
            setJudgeModel={props.setJudgeModel}
            powerfulModel={props.powerfulModel}
            setPowerfulModel={props.setPowerfulModel}
            temperature={props.temperature}
            setTemperature={props.setTemperature}
            ocr={props.ocr}
            setOcr={props.setOcr}
            correctionIterations={props.correctionIterations}
            setCorrectionIterations={props.setCorrectionIterations}
          />
        </ExpandableSection>
        <Button
          variant="primary"
          onClick={(e) => {
            e.preventDefault();
            void props.extractPrescriptionData();
          }}
          loading={
            props.status !== '' &&
            props.status !== 'Error' &&
            props.status !== 'FAILED'
          }
          disabled={
            props.imageFiles.length !== 1 ||
            props.schema === '' ||
            (props.status !== '' &&
              props.status !== 'Error' &&
              props.status !== 'FAILED')
          }
          loadingText={
            props.extractPrescription.data?.getJobStatus?.status
              ? `${props.extractPrescription.data?.getJobStatus?.status}: ${props.extractPrescription.data?.getJobStatus?.state ?? ''}`
              : props.status
          }
        >
          {props.status === '' ||
          props.status === 'Error' ||
          props.status == 'FAILED'
            ? 'Extract'
            : props.status}
        </Button>
      </SpaceBetween>
    </Container>
  );
};

export default NewPrescriptionForm;
