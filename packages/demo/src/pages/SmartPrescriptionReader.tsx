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
  ContentLayout,
  Grid,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useEffect, useState } from 'react';
import DisplayPrescription from '../components/DisplayPrescription';
import NewPrescriptionForm from '../components/NewPrescriptionForm';
import PrescriptionForm from '../components/PrescriptionForm';
import { usePrescriptionExtraction } from '../hooks/usePrescriptionExtraction';
import StateProgress from '../components/StateProgress';

const SmartPrescriptionReader = () => {
  const [prescriptionData, setPrescriptionData] = useState<
    object | object[] | undefined
  >(undefined);
  const {
    imageFiles,
    setImageFiles,
    schema,
    setSchema,
    fastModel,
    setFastModel,
    judgeModel,
    setJudgeModel,
    powerfulModel,
    setPowerfulModel,
    temperature,
    setTemperature,
    ocr,
    setOcr,
    correctionIterations,
    setCorrectionIterations,
    status,
    stateLog,
    handleReset,
    extractPrescription,
    extractPrescriptionData,
  } = usePrescriptionExtraction(setPrescriptionData);

  useEffect(() => {
    console.log('prescriptionData', prescriptionData);
  }, [prescriptionData]);

  return (
    <ContentLayout
      header={
        <SpaceBetween size="m">
          <Header
            variant="h1"
            description="Extract details from prescription images"
            actions={<Button onClick={handleReset}>New Prescription</Button>}
          >
            Smart Prescription Reader
          </Header>
        </SpaceBetween>
      }
    >
      <SpaceBetween size={'xl'}>
        {stateLog.length > 0 && <StateProgress stateLog={stateLog} />}

        {extractPrescription.data?.getJobStatus?.status === 'COMPLETED' && (
          <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
            <DisplayPrescription imageFile={imageFiles[0]} />
            <PrescriptionForm data={prescriptionData} schema={schema} />
          </Grid>
        )}

        {extractPrescription.data?.getJobStatus?.status !== 'COMPLETED' && (
          <NewPrescriptionForm
            imageFiles={imageFiles}
            setImageFiles={setImageFiles}
            schema={schema}
            setSchema={setSchema}
            fastModel={fastModel}
            setFastModel={setFastModel}
            judgeModel={judgeModel}
            setJudgeModel={setJudgeModel}
            powerfulModel={powerfulModel}
            setPowerfulModel={setPowerfulModel}
            temperature={temperature}
            setTemperature={setTemperature}
            ocr={ocr}
            setOcr={setOcr}
            correctionIterations={correctionIterations}
            setCorrectionIterations={setCorrectionIterations}
            extractPrescriptionData={extractPrescriptionData}
            status={status}
            extractPrescription={extractPrescription}
          />
        )}
      </SpaceBetween>
    </ContentLayout>
  );
};

export default SmartPrescriptionReader;
