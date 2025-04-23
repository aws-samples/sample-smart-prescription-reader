/* eslint-disable */
import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  AWSDate: { input: any; output: any; }
  AWSDateTime: { input: any; output: any; }
  AWSEmail: { input: any; output: any; }
  AWSIPAddress: { input: any; output: any; }
  AWSJSON: { input: any; output: any; }
  AWSPhone: { input: any; output: any; }
  AWSTime: { input: any; output: any; }
  AWSTimestamp: { input: any; output: any; }
  AWSURL: { input: any; output: any; }
};

export type ErrorDetail = {
  __typename?: 'ErrorDetail';
  code: Scalars['String']['output'];
  message: Scalars['String']['output'];
};

export type JobStateEnum =
  | 'CORRECT'
  | 'EXTRACT'
  | 'JUDGE'
  | 'TRANSCRIBE';

export type JobStatusEnum =
  | 'COMPLETED'
  | 'FAILED'
  | 'PROCESSING'
  | 'QUEUED';

export type ModelUsage = {
  __typename?: 'ModelUsage';
  cacheReadInputTokens?: Maybe<Scalars['Int']['output']>;
  inputTokens: Scalars['Int']['output'];
  outputTokens?: Maybe<Scalars['Int']['output']>;
  task?: Maybe<Scalars['String']['output']>;
};

export type Mutation = {
  __typename?: 'Mutation';
  processPrescription: PrescriptionJob;
  requestUploadFile: PresignedUrlResponse;
};


export type MutationProcessPrescriptionArgs = {
  input: ProcessPrescriptionInput;
};


export type MutationRequestUploadFileArgs = {
  input: RequestUploadFileInput;
};

export type PrescriptionJob = {
  __typename?: 'PrescriptionJob';
  createdAt: Scalars['AWSDateTime']['output'];
  error?: Maybe<ErrorDetail>;
  jobId: Scalars['ID']['output'];
  message?: Maybe<Scalars['String']['output']>;
  owner?: Maybe<Scalars['String']['output']>;
  prescriptionData?: Maybe<Scalars['AWSJSON']['output']>;
  score?: Maybe<Scalars['String']['output']>;
  state?: Maybe<JobStateEnum>;
  status: JobStatusEnum;
  ttl: Scalars['Int']['output'];
  updatedAt: Scalars['AWSDateTime']['output'];
  usage?: Maybe<Array<Maybe<ModelUsage>>>;
};

export type PresignedUrlResponse = {
  __typename?: 'PresignedUrlResponse';
  objectKey?: Maybe<Scalars['String']['output']>;
  url: Scalars['String']['output'];
};

export type ProcessPrescriptionInput = {
  fastModel?: InputMaybe<Scalars['String']['input']>;
  image: Scalars['String']['input'];
  judgeModel?: InputMaybe<Scalars['String']['input']>;
  maxCorrections?: InputMaybe<Scalars['Int']['input']>;
  powerfulModel?: InputMaybe<Scalars['String']['input']>;
  prescriptionSchema: Scalars['String']['input'];
  temperature?: InputMaybe<Scalars['Float']['input']>;
  useTextract?: InputMaybe<Scalars['Boolean']['input']>;
};

export type Query = {
  __typename?: 'Query';
  getJobStatus: PrescriptionJob;
};


export type QueryGetJobStatusArgs = {
  jobId: Scalars['String']['input'];
};

export type RequestUploadFileInput = {
  expiration?: InputMaybe<Scalars['Int']['input']>;
  fileName: Scalars['String']['input'];
};

export type ProcessPrescriptionMutationVariables = Exact<{
  input: ProcessPrescriptionInput;
}>;


export type ProcessPrescriptionMutation = { __typename?: 'Mutation', processPrescription: { __typename?: 'PrescriptionJob', createdAt: any, jobId: string, status: JobStatusEnum, updatedAt: any } };

export type RequestUploadFileMutationVariables = Exact<{
  input: RequestUploadFileInput;
}>;


export type RequestUploadFileMutation = { __typename?: 'Mutation', requestUploadFile: { __typename?: 'PresignedUrlResponse', url: string, objectKey?: string | null } };

export type GetJobStatusQueryVariables = Exact<{
  jobId: Scalars['String']['input'];
}>;


export type GetJobStatusQuery = { __typename?: 'Query', getJobStatus: { __typename?: 'PrescriptionJob', jobId: string, status: JobStatusEnum, state?: JobStateEnum | null, message?: string | null, prescriptionData?: any | null, score?: string | null, updatedAt: any, error?: { __typename?: 'ErrorDetail', code: string, message: string } | null, usage?: Array<{ __typename?: 'ModelUsage', inputTokens: number, outputTokens?: number | null, cacheReadInputTokens?: number | null, task?: string | null } | null> | null } };


export const ProcessPrescriptionDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"ProcessPrescription"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ProcessPrescriptionInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"processPrescription"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"jobId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<ProcessPrescriptionMutation, ProcessPrescriptionMutationVariables>;
export const RequestUploadFileDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"RequestUploadFile"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"RequestUploadFileInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"requestUploadFile"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"url"}},{"kind":"Field","name":{"kind":"Name","value":"objectKey"}}]}}]}}]} as unknown as DocumentNode<RequestUploadFileMutation, RequestUploadFileMutationVariables>;
export const GetJobStatusDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetJobStatus"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"jobId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"getJobStatus"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"jobId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"jobId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"jobId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"state"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"prescriptionData"}},{"kind":"Field","name":{"kind":"Name","value":"score"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}},{"kind":"Field","name":{"kind":"Name","value":"error"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"code"}},{"kind":"Field","name":{"kind":"Name","value":"message"}}]}},{"kind":"Field","name":{"kind":"Name","value":"usage"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"inputTokens"}},{"kind":"Field","name":{"kind":"Name","value":"outputTokens"}},{"kind":"Field","name":{"kind":"Name","value":"cacheReadInputTokens"}},{"kind":"Field","name":{"kind":"Name","value":"task"}}]}}]}}]}}]} as unknown as DocumentNode<GetJobStatusQuery, GetJobStatusQueryVariables>;