/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import {
  GetJobStatusDocument,
  GetJobStatusQuery,
  JobStateEnum,
  ModelUsage,
  PrescriptionJob,
  ProcessPrescriptionDocument,
  ProcessPrescriptionInput,
  RequestUploadFileDocument,
  RequestUploadFileInput,
} from ':smart-prescription-reader/models-graphql';
import {
  useMutation,
  useQuery,
  UseQueryResult,
  Query,
} from '@tanstack/react-query';
import { useState } from 'react';
import { useGlobalUIContext } from './useGlobalUIContext';
import { prepareImages } from '../components/resizeImages';
import { useGraphqlClient } from './useGraphqlClient';
import Ajv from 'ajv';
import { StatusIndicatorProps } from '@cloudscape-design/components';

export interface S3Image {
  data: Blob;
  type: string;
  key: string;
}

export interface StateLogEntry {
  state: JobStateEnum;
  status: StatusIndicatorProps.Type;
  score?: string;
  usage?: ModelUsage;
}

export interface UsePrescriptionExtractionType {
  imageFiles: File[];
  setImageFiles: React.Dispatch<React.SetStateAction<File[]>>;
  schema: string;
  setSchema: React.Dispatch<React.SetStateAction<string>>;
  ocr: boolean;
  setOcr: React.Dispatch<React.SetStateAction<boolean>>;
  correctionIterations: number;
  setCorrectionIterations: React.Dispatch<React.SetStateAction<number>>;
  fastModel: string;
  setFastModel: React.Dispatch<React.SetStateAction<string>>;
  judgeModel: string;
  setJudgeModel: React.Dispatch<React.SetStateAction<string>>;
  powerfulModel: string;
  setPowerfulModel: React.Dispatch<React.SetStateAction<string>>;
  temperature: number;
  setTemperature: React.Dispatch<React.SetStateAction<number>>;
  status: string;
  setStatus: React.Dispatch<React.SetStateAction<string>>;
  stateLog: StateLogEntry[];
  extractPrescriptionData: () => Promise<void>;
  extractPrescription: UseQueryResult<GetJobStatusQuery, Error>;
  handleReset: () => void;
}

export const defaultTemperature = 0.0;
export const defaultFastModel = 'us.anthropic.claude-3-haiku-20240307-v1:0';
export const defaultJudgeModel = 'us.amazon.nova-pro-v1:0';
export const defaultPowerfulModel =
  'us.anthropic.claude-3-7-sonnet-20250219-v1:0';
export const defaultCorrectionIterations = 1;
export const defaultOcr = true;

export const usePrescriptionExtraction = (
  setPrescriptionData: React.Dispatch<React.SetStateAction<object | object[]>>,
): UsePrescriptionExtractionType => {
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [fastModel, setFastModel] = useState<string>(defaultFastModel);
  const [judgeModel, setJudgeModel] = useState<string>(defaultJudgeModel);
  const [powerfulModel, setPowerfulModel] =
    useState<string>(defaultPowerfulModel);
  const [temperature, setTemperature] = useState<number>(defaultTemperature);
  const [schema, setSchema] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [jobId, setJobId] = useState<string | undefined>(undefined);
  const [stateLog, setStateLog] = useState<StateLogEntry[]>([]);
  const [ocr, setOcr] = useState<boolean>(defaultOcr);
  const [correctionIterations, setCorrectionIterations] = useState<number>(
    defaultCorrectionIterations,
  );

  const { addFlashItem } = useGlobalUIContext();

  const graphqlClient = useGraphqlClient();

  const ajv = new Ajv();

  const validatePrescriptionData = (prescriptionData: any) => {
    const validate = ajv.compile(JSON.parse(schema));

    const data: object | object[] =
      typeof prescriptionData === 'string'
        ? JSON.parse(prescriptionData)
        : prescriptionData;
    const valid = validate(data);
    if (!valid) {
      console.log(validate.errors);
      addFlashItem({
        type: 'error',
        content: 'Failed to validate prescription data',
      });
      setStatus('Error');
      throw new Error('Failed to validate prescription data');
    }
    setPrescriptionData(data);
  };

  const updateStateLog = (job: PrescriptionJob) => {
    if (!job.state) return;

    const getStatus = (status: string): StatusIndicatorProps.Type => {
      switch (status) {
        case 'COMPLETED':
          return 'success';
        case 'FAILED':
          return 'error';
        default:
          return 'in-progress';
      }
    };

    setStateLog((prev) => {
      const newEntry: StateLogEntry = {
        state: job.state!,
        status: getStatus(job.status),
        score:
          job.score && job.state === 'JUDGE' && job.status === 'COMPLETED'
            ? job.score
            : undefined,
        usage:
          job.usage &&
          job.status === 'COMPLETED' &&
          job.state === job.usage[job.usage.length - 1]?.task
            ? job.usage[job.usage.length - 1]!
            : undefined,
      };

      if (prev.length === 0) return [newEntry];

      const lastEntry = prev[prev.length - 1];

      // Create new array only when necessary
      const updatedPrev = [...prev];
      const lastIndex = updatedPrev.length - 1;

      if (newEntry.state === lastEntry.state) {
        updatedPrev[lastIndex] = newEntry;
        return updatedPrev;
      }

      updatedPrev[lastIndex].status = 'success';

      if (
        job.usage &&
        lastEntry.state === job.usage[job.usage.length - 1]?.task &&
        !lastEntry.usage
      ) {
        updatedPrev[lastIndex].usage = job.usage[job.usage.length - 1]!;
      }

      if (lastEntry.state === 'JUDGE' && job.score && !lastEntry.score) {
        updatedPrev[lastIndex].score = job.score;
      }

      return [...updatedPrev, newEntry];
    });
  };

  const refetchInterval = (
    query: Query<
      GetJobStatusQuery,
      Error,
      GetJobStatusQuery,
      (string | undefined)[]
    >,
  ) => {
    if (
      query.state.data?.getJobStatus?.status &&
      ['FAILED', 'COMPLETED'].includes(query.state.data.getJobStatus.status)
    ) {
      return false;
    } else {
      return 5000;
    }
  };

  const extractPrescription = useQuery({
    queryKey: ['prescriptionJob', jobId],
    queryFn: async () => {
      const response = await graphqlClient(GetJobStatusDocument, {
        jobId: jobId!,
      });
      if (response.getJobStatus) {
        updateStateLog(response.getJobStatus as PrescriptionJob);
      }
      if (
        response.getJobStatus?.status === 'COMPLETED' &&
        response.getJobStatus.prescriptionData
      ) {
        validatePrescriptionData(response.getJobStatus.prescriptionData);
      }
      if (response.getJobStatus?.status === 'FAILED') {
        console.log(
          'Failed to extract prescription data',
          response.getJobStatus.error,
        );
        setStatus('Error');
        addFlashItem({
          type: 'error',
          content: `Failed to extract prescription data: ${response.getJobStatus.error?.code}`,
        });
      }
      if (response.getJobStatus?.status) {
        setStatus(response.getJobStatus.status);
      }

      return response;
    },
    refetchInterval: (query) => refetchInterval(query),
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: (query) => {
      if (
        query.state.data?.getJobStatus?.status &&
        ['FAILED', 'COMPLETED'].includes(query.state.data.getJobStatus.status)
      ) {
        return false;
      } else {
        return true;
      }
    },
    enabled: !!jobId,
  });

  const processPrescription = useMutation({
    mutationFn: (input: ProcessPrescriptionInput) =>
      graphqlClient(ProcessPrescriptionDocument, { input }),
    onError: (error) => {
      console.log('mutationerror', error);
      setStatus('Error');
      addFlashItem({
        type: 'error',
        content: 'Failed to extract prescription data',
      });
    },
  });

  const putFile = async (
    url?: string,
    body?: BodyInit,
    headers?: HeadersInit,
  ) => {
    if (!url) {
      return;
    }

    const response = await window.fetch(new URL(url), {
      method: 'PUT',
      headers,
      body,
    });

    if (!response.ok) {
      console.error(`Uploading failed: ${response.status}`);
      throw new Error();
    }
  };

  const uploadImage = useMutation({
    mutationFn: (input: RequestUploadFileInput) =>
      graphqlClient(RequestUploadFileDocument, { input }),
    onError: (err) => {
      console.error(`Failed to upload images: ${JSON.stringify(err)}`);
      addFlashItem({ type: 'error', content: 'Failed to upload image!' });
    },
  });

  /**
   * Uploads an image to S3, returns the object key it was uploaded to.
   **/
  async function uploadImageToS3(image: S3Image): Promise<string> {
    return uploadImage
      .mutateAsync({
        fileName: image.key,
      })
      .then(async ({ requestUploadFile: { url, objectKey } }) => {
        if (!objectKey) {
          throw new Error('objectKey should have been populated');
        }

        console.log(`Generated url for ${image.key}`);
        try {
          await putFile(
            url,
            image.data,
            new Headers({ 'Content-type': image.type }),
          );
          return objectKey;
        } catch (e) {
          console.log(`Failed to upload ${image.key}`);
          throw e;
        }
      })
      .catch((error) => {
        console.log(`Failed to upload ${image.key}`);
        throw error;
      });
  }

  async function handleReset() {
    setImageFiles([]);
    processPrescription.reset();
    setJobId(undefined);
    setStatus('');
    setStateLog([]);
  }

  async function extractPrescriptionData() {
    console.log('Extracting prescription data');
    const objectKeys: string[] = [];
    console.log('Prepare images for upload');
    setStatus('Preparing');
    const images = await prepareImages(imageFiles);

    console.log('Upload images to S3');
    setStatus('Uploading');

    const imageKeys: S3Image[] = images.map((img) => {
      return {
        data: img.data,
        type: img.type,
        key: img.name,
      };
    });
    const uploads = imageKeys.map(uploadImageToS3);
    try {
      objectKeys.push(...(await Promise.all(uploads)));
    } catch (e) {
      console.log('Failed to upload images');
      setStatus('Error');
      addFlashItem({
        type: 'error',
        content: 'Failed to upload images',
      });
      return;
    }

    console.log(`Uploaded images: ${JSON.stringify(objectKeys)}`);
    setStatus('Extracting');
    try {
      processPrescription.mutate(
        {
          image: objectKeys[0],
          prescriptionSchema: schema,
          temperature,
          fastModel,
          judgeModel,
          powerfulModel,
          useTextract: ocr,
          maxCorrections: correctionIterations,
        },
        {
          onSuccess: (data) => {
            console.log('mutation success', data);
            setJobId(data.processPrescription.jobId);
          },
        },
      );
    } catch (e) {
      console.log('caught error on processPrescription mutation', e);
    }
  }

  return {
    imageFiles,
    setImageFiles,
    schema,
    setSchema,
    ocr,
    setOcr,
    correctionIterations,
    setCorrectionIterations,
    fastModel,
    setFastModel,
    judgeModel,
    setJudgeModel,
    powerfulModel,
    setPowerfulModel,
    temperature,
    setTemperature,
    status,
    setStatus,
    stateLog,
    extractPrescriptionData,
    extractPrescription,
    handleReset,
  };
};
