# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from smart_prescription_reader.models import (
    ErrorDetail,
    JobStateEnum,
    JobStatusEnum,
    ModelUsage,
)


class ExtractPrescriptionInput(BaseModel):
    image: str = Field(description="S3 key of the image")
    prescription_schema: str = Field(alias="prescriptionSchema", description="JSON Schema to use for extraction")
    ocr_transcription: Optional[str] = Field(
        default=None,
        alias="ocrTranscription",
        description="Result of OCR from the image",
    )
    temperature: Optional[float] = Field(default=None, description="Temperature for the model")
    model: Optional[str] = Field(default=None, description="Fast model to use for extraction")
    model_config = ConfigDict(populate_by_name=True)


class ExtractPrescriptionResult(BaseModel):
    is_handwritten: bool = Field(alias="isHandwritten", description="Whether the prescription is handwritten")
    is_prescription: bool = Field(alias="isPrescription", description="Whether the image is a prescription")
    extraction: dict = Field(description="Result of extraction from the image")
    usage: ModelUsage = Field(description="Tokens used by the model")
    model_config = ConfigDict(populate_by_name=True)


class EvaluateResponseInput(BaseModel):
    image: str = Field(description="S3 key of the image")
    prescription_schema: str = Field(alias="prescriptionSchema", description="JSON Schema to use for extraction")
    extraction: dict = Field(description="Result of extraction from the image")
    ocr_transcription: Optional[str] = Field(
        default=None,
        alias="ocrTranscription",
        description="Result of OCR from the image",
    )
    temperature: Optional[float] = Field(default=None, description="Temperature for the model")
    model: Optional[str] = Field(
        default=None,
        description="Judge model to use for evaluation",
    )
    model_config = ConfigDict(populate_by_name=True)


class ExtractionQuality(str, Enum):
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class EvaluateResponseResult(BaseModel):
    score: ExtractionQuality = Field(description="Score of the evaluation")
    feedback: str = Field(description="Feedback from the evaluation to correct the extraction")
    usage: ModelUsage = Field(description="Tokens used by the model")

    model_config = ConfigDict(populate_by_name=True)


class OcrInput(BaseModel):
    image: str = Field(description="S3 key of the image")
    model_config = ConfigDict(populate_by_name=True)


class OcrResult(BaseModel):
    transcription: str = Field(description="Transcription of the image")
    model_config = ConfigDict(populate_by_name=True)


class CorrectResponseInput(BaseModel):
    image: str = Field(description="S3 key of the image")
    prescription_schema: str = Field(alias="prescriptionSchema", description="JSON Schema to use for extraction")
    extraction: dict = Field(description="Result of extraction from the image")
    ocr_transcription: Optional[str] = Field(
        default=None,
        alias="ocrTranscription",
        description="Result of OCR from the image",
    )
    feedback: str = Field(description="Feedback from the evaluation to correct the extraction")
    temperature: Optional[float] = Field(default=None, description="Temperature for the model")
    model: Optional[str] = Field(
        default=None,
        description="Powerful model to use for extraction",
    )

    model_config = ConfigDict(populate_by_name=True)


class CorrectResponseResult(BaseModel):
    extraction: dict = Field(description="Result of extraction from the image")
    usage: ModelUsage = Field(description="Tokens used by the model")

    model_config = ConfigDict(populate_by_name=True)


class UpdateJobStatusInput(BaseModel):
    job_id: str = Field(..., alias="jobId")
    status: JobStatusEnum = Field(..., description="Status of the job")
    state: Optional[JobStateEnum] = Field(default=None, description="State of the job")
    message: Optional[str] = Field(default=None, description="Message of the job")
    usage: Optional[list[ModelUsage]] = Field(default=None, description="Usage of the job")
    prescription_data: Optional[dict] = Field(default=None, alias="prescriptionData", description="Prescription data")
    score: Optional[str] = Field(default=None, description="Score of the job")
    error: Optional[ErrorDetail] = Field(default=None, description="Error of the job")
    model_config = ConfigDict(populate_by_name=True)


class UpdatePrescriptionJobInput(BaseModel):
    job_id: str = Field(alias="jobId")
    status: JobStatusEnum
    state: Optional[JobStateEnum] = None
    message: Optional[str] = None
    usage: Optional[list[Optional[ModelUsage]]] = None
    prescription_data: Optional[str] = Field(alias="prescriptionData", default=None)
    score: Optional[str] = None
    error: Optional[ErrorDetail] = None
