/* eslint-disable */
import * as types from './graphql.js';
import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';

/**
 * Map of all GraphQL operations in the project.
 *
 * This map has several performance disadvantages:
 * 1. It is not tree-shakeable, so it will include all operations in the project.
 * 2. It is not minifiable, so the string of a GraphQL query will be multiple times inside the bundle.
 * 3. It does not support dead code elimination, so it will add unused operations.
 *
 * Therefore it is highly recommended to use the babel or swc plugin for production.
 * Learn more about it here: https://the-guild.dev/graphql/codegen/plugins/presets/preset-client#reducing-bundle-size
 */
type Documents = {
    "mutation ProcessPrescription($input: ProcessPrescriptionInput!) {\n  processPrescription(input: $input) {\n    createdAt\n    jobId\n    status\n    updatedAt\n  }\n}": typeof types.ProcessPrescriptionDocument,
    "mutation RequestUploadFile($input: RequestUploadFileInput!) {\n  requestUploadFile(input: $input) {\n    url\n    objectKey\n  }\n}": typeof types.RequestUploadFileDocument,
    "query GetJobStatus($jobId: String!) {\n  getJobStatus(jobId: $jobId) {\n    jobId\n    status\n    state\n    message\n    prescriptionData\n    score\n    updatedAt\n    error {\n      code\n      message\n    }\n    usage {\n      inputTokens\n      outputTokens\n      cacheReadInputTokens\n      task\n    }\n  }\n}": typeof types.GetJobStatusDocument,
};
const documents: Documents = {
    "mutation ProcessPrescription($input: ProcessPrescriptionInput!) {\n  processPrescription(input: $input) {\n    createdAt\n    jobId\n    status\n    updatedAt\n  }\n}": types.ProcessPrescriptionDocument,
    "mutation RequestUploadFile($input: RequestUploadFileInput!) {\n  requestUploadFile(input: $input) {\n    url\n    objectKey\n  }\n}": types.RequestUploadFileDocument,
    "query GetJobStatus($jobId: String!) {\n  getJobStatus(jobId: $jobId) {\n    jobId\n    status\n    state\n    message\n    prescriptionData\n    score\n    updatedAt\n    error {\n      code\n      message\n    }\n    usage {\n      inputTokens\n      outputTokens\n      cacheReadInputTokens\n      task\n    }\n  }\n}": types.GetJobStatusDocument,
};

/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 *
 *
 * @example
 * ```ts
 * const query = graphql(`query GetUser($id: ID!) { user(id: $id) { name } }`);
 * ```
 *
 * The query argument is unknown!
 * Please regenerate the types.
 */
export function graphql(source: string): unknown;

/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "mutation ProcessPrescription($input: ProcessPrescriptionInput!) {\n  processPrescription(input: $input) {\n    createdAt\n    jobId\n    status\n    updatedAt\n  }\n}"): (typeof documents)["mutation ProcessPrescription($input: ProcessPrescriptionInput!) {\n  processPrescription(input: $input) {\n    createdAt\n    jobId\n    status\n    updatedAt\n  }\n}"];
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "mutation RequestUploadFile($input: RequestUploadFileInput!) {\n  requestUploadFile(input: $input) {\n    url\n    objectKey\n  }\n}"): (typeof documents)["mutation RequestUploadFile($input: RequestUploadFileInput!) {\n  requestUploadFile(input: $input) {\n    url\n    objectKey\n  }\n}"];
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query GetJobStatus($jobId: String!) {\n  getJobStatus(jobId: $jobId) {\n    jobId\n    status\n    state\n    message\n    prescriptionData\n    score\n    updatedAt\n    error {\n      code\n      message\n    }\n    usage {\n      inputTokens\n      outputTokens\n      cacheReadInputTokens\n      task\n    }\n  }\n}"): (typeof documents)["query GetJobStatus($jobId: String!) {\n  getJobStatus(jobId: $jobId) {\n    jobId\n    status\n    state\n    message\n    prescriptionData\n    score\n    updatedAt\n    error {\n      code\n      message\n    }\n    usage {\n      inputTokens\n      outputTokens\n      cacheReadInputTokens\n      task\n    }\n  }\n}"];

export function graphql(source: string) {
  return (documents as any)[source] ?? {};
}

export type DocumentType<TDocumentNode extends DocumentNode<any, any>> = TDocumentNode extends DocumentNode<  infer TType,  any>  ? TType  : never;