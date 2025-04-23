from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobStateEnum(str, Enum):
    TRANSCRIBE = "TRANSCRIBE"
    EXTRACT = "EXTRACT"
    JUDGE = "JUDGE"
    CORRECT = "CORRECT"


class JobStatusEnum(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessPrescriptionInput(BaseModel):
    image: str
    prescription_schema: str = Field(alias="prescriptionSchema")
    temperature: Optional[float] = None
    fast_model: Optional[str] = Field(alias="fastModel", default=None)
    judge_model: Optional[str] = Field(alias="judgeModel", default=None)
    powerful_model: Optional[str] = Field(alias="powerfulModel", default=None)
    use_textract: Optional[bool] = Field(alias="useTextract", default=None)
    max_corrections: Optional[int] = Field(alias="maxCorrections", default=None)


class RequestUploadFileInput(BaseModel):
    file_name: str = Field(alias="fileName")
    expiration: Optional[int] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ModelUsage(BaseModel):
    input_tokens: int = Field(alias="inputTokens")
    output_tokens: Optional[int] = Field(default=None, alias="outputTokens")
    cache_read_input_tokens: Optional[int] = Field(
        default=None, alias="cacheReadInputTokens"
    )
    task: Optional[str] = Field(default=None)


class PrescriptionJob(BaseModel):
    created_at: datetime = Field(alias="createdAt")
    error: Optional[ErrorDetail] = Field(default=None)
    job_id: str = Field(alias="jobId")
    message: Optional[str] = Field(default=None)
    owner: Optional[str] = Field(default=None)
    prescription_data: Optional[str] = Field(default=None, alias="prescriptionData")
    score: Optional[str] = Field(default=None)
    state: Optional[JobStateEnum] = Field(default=None)
    status: JobStatusEnum
    ttl: int
    updated_at: datetime = Field(alias="updatedAt")
    usage: Optional[List[Optional[ModelUsage]]] = Field(default=None)


class PresignedUrlResponse(BaseModel):
    object_key: Optional[str] = Field(default=None, alias="objectKey")
    url: str


class Mutation(BaseModel):
    process_prescription: PrescriptionJob = Field(alias="processPrescription")
    request_upload_file: PresignedUrlResponse = Field(alias="requestUploadFile")


class Query(BaseModel):
    get_job_status: PrescriptionJob = Field(alias="getJobStatus")


class RequestUploadFileRequestuploadfile(BaseModel):
    typename: Literal["PresignedUrlResponse"] = Field(
        alias="__typename", default="PresignedUrlResponse"
    )
    url: str
    object_key: Optional[str] = Field(default=None, alias="objectKey")


class RequestUploadFile(BaseModel):
    request_upload_file: RequestUploadFileRequestuploadfile = Field(
        alias="requestUploadFile"
    )

    class Arguments(BaseModel):
        input: RequestUploadFileInput

    class Meta:
        document = "mutation RequestUploadFile($input: RequestUploadFileInput!) {\n  requestUploadFile(input: $input) {\n    url\n    objectKey\n    __typename\n  }\n}"


class ProcessPrescriptionProcessprescription(BaseModel):
    typename: Literal["PrescriptionJob"] = Field(
        alias="__typename", default="PrescriptionJob"
    )
    created_at: datetime = Field(alias="createdAt")
    job_id: str = Field(alias="jobId")
    status: JobStatusEnum
    updated_at: datetime = Field(alias="updatedAt")


class ProcessPrescription(BaseModel):
    process_prescription: ProcessPrescriptionProcessprescription = Field(
        alias="processPrescription"
    )

    class Arguments(BaseModel):
        input: ProcessPrescriptionInput

    class Meta:
        document = "mutation ProcessPrescription($input: ProcessPrescriptionInput!) {\n  processPrescription(input: $input) {\n    createdAt\n    jobId\n    status\n    updatedAt\n    __typename\n  }\n}"


class GetJobStatusGetjobstatusError(BaseModel):
    typename: Literal["ErrorDetail"] = Field(alias="__typename", default="ErrorDetail")
    code: str
    message: str


class GetJobStatusGetjobstatusUsage(BaseModel):
    typename: Literal["ModelUsage"] = Field(alias="__typename", default="ModelUsage")
    input_tokens: int = Field(alias="inputTokens")
    output_tokens: Optional[int] = Field(default=None, alias="outputTokens")
    cache_read_input_tokens: Optional[int] = Field(
        default=None, alias="cacheReadInputTokens"
    )
    task: Optional[str] = Field(default=None)


class GetJobStatusGetjobstatus(BaseModel):
    typename: Literal["PrescriptionJob"] = Field(
        alias="__typename", default="PrescriptionJob"
    )
    job_id: str = Field(alias="jobId")
    status: JobStatusEnum
    state: Optional[JobStateEnum] = Field(default=None)
    message: Optional[str] = Field(default=None)
    prescription_data: Optional[str] = Field(default=None, alias="prescriptionData")
    score: Optional[str] = Field(default=None)
    updated_at: datetime = Field(alias="updatedAt")
    error: Optional[GetJobStatusGetjobstatusError] = Field(default=None)
    usage: Optional[List[Optional[GetJobStatusGetjobstatusUsage]]] = Field(default=None)


class GetJobStatus(BaseModel):
    get_job_status: GetJobStatusGetjobstatus = Field(alias="getJobStatus")

    class Arguments(BaseModel):
        job_id: str = Field(alias="jobId")

    class Meta:
        document = "query GetJobStatus($jobId: String!) {\n  getJobStatus(jobId: $jobId) {\n    jobId\n    status\n    state\n    message\n    prescriptionData\n    score\n    updatedAt\n    error {\n      code\n      message\n      __typename\n    }\n    usage {\n      inputTokens\n      outputTokens\n      cacheReadInputTokens\n      task\n      __typename\n    }\n    __typename\n  }\n}"
