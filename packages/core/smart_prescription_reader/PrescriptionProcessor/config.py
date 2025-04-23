# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import logging
from typing import TYPE_CHECKING, Optional

import botocore.exceptions
from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient

logger = logging.getLogger(__name__)


class PrescriptionReaderConfig(BaseModel):
    @staticmethod
    def model_validate_ssm(ssm_client: "SSMClient", parameter: str) -> "PrescriptionReaderConfig":
        if not hasattr(PrescriptionReaderConfig.model_validate_ssm, "_instance"):
            try:
                response = ssm_client.get_parameter(Name=parameter)
                value = response["Parameter"]["Value"]
                PrescriptionReaderConfig.model_validate_ssm._instance = PrescriptionReaderConfig.model_validate_json(
                    value
                )
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "ParameterNotFound":
                    logger.error(f"SSM Parameter not found {parameter}")
                    PrescriptionReaderConfig.model_validate_ssm._instance = PrescriptionReaderConfig()
                else:
                    raise e

        return PrescriptionReaderConfig.model_validate_ssm._instance

    model_id: Optional[str] = Field(
        default="us.anthropic.claude-3-haiku-20240307-v1:0",
        description="The model to use for the prescription reader",
        alias="modelId",
    )
    temperature: Optional[float] = Field(
        default=0.0,
        description="The temperature to use for the prescription reader",
        alias="temperature",
    )
    medications_key: Optional[str] = Field(
        default=None,
        description="The key to the medications file in S3",
        alias="medicationsKey",
    )
    glossary_key: Optional[str] = Field(
        default=None,
        description="The key to the glossary file in S3",
        alias="glossaryKey",
    )
    thinking: Optional[bool] = Field(
        default=False,
        description="Chain of thought",
        alias="thinking",
    )
    transcribe: Optional[bool] = Field(
        default=False,
        description="Transcribe the prescription",
        alias="transcribe",
    )
    prompt_cache_models: Optional[list[str]] = Field(
        default=None,
        description="List of models to cache prompts for",
        alias="promptCacheModels",
    )

    @model_validator(mode="after")
    def validate_prompt_cache(self) -> "PrescriptionReaderConfig":
        if self.prompt_cache_models is None:
            self.prompt_cache_models = [
                "anthropic.claude-3-7-sonnet-20250219-v1:0",
                "anthropic.claude-3-5-haiku-20241022-v1:0",
                "amazon.nova-micro-v1:0",
                "amazon.nova-lite-v1:0",
                "amazon.nova-pro-v1:0",
            ]
        return self

    def prompt_cache(self, model_id: str = None) -> bool:
        if model_id is None:
            model_id = self.model_id
        return any(model in model_id for model in self.prompt_cache_models)
