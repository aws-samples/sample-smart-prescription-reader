# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

import json_repair
import jsonschema

from smart_prescription_reader.bedrock_runtime_client import (
    build_full_response,
    invoke_model_with_input,
    retry_bedrock_errors,
)
from smart_prescription_reader.exceptions import (
    InvalidImageContentsError,
    ModelResponseError,
)
from smart_prescription_reader.models import ModelUsage
from smart_prescription_reader.models.workflow import ExtractPrescriptionResult
from smart_prescription_reader.PrescriptionProcessor.processor import (
    PrescriptionProcessor,
    logger,
)
from smart_prescription_reader.utils import extract_tag_value

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.type_defs import ContentBlockTypeDef

logger = logging.getLogger(__name__)


def get_is_prescription(text: str) -> bool:
    """
    Find the value between '<isprescription>' tags and convert to a boolean.

    Args:
        text: String containing XML-style tags with prescription status

    Returns:
        bool: True if the value between tags is 'true' (case-insensitive), False otherwise
    """
    value = extract_tag_value(text, "isprescription")
    return value.lower() == "true"


def get_is_handwritten(text: str) -> bool:
    """
    Find the value between '<ishandwritten>' tags and convert to a boolean.

    Args:
        text: String containing XML-style tags with handwritten status

    Returns:
        bool: True if the value between tags is 'true' (case-insensitive), False otherwise
    """
    value = extract_tag_value(text, "ishandwritten")
    return value.lower() == "true"


def get_prescription_data(text: str) -> dict[str, Any]:
    """
    Find the value between '<prescriptiondata>' tags and convert to a dictionary.

    Args:
        text: String containing XML-style tags with prescription data

    Returns:
        dict: Dictionary containing prescription data
    """
    value = extract_tag_value(text, "prescriptiondata")
    return json_repair.loads(value)


class ExtractPrescription(PrescriptionProcessor):
    """Class for handling prescription extraction operations."""

    task = "EXTRACT"

    def prepare_extract_conversation(
            self,
            image: "ContentBlockTypeDef",
            prescription_schema: dict[str, Any],
            ocr_transcription: Optional[str] = None,
            response_prefill: Optional[str] = None,
    ) -> dict[str, Any]:
        """Prepare the conversation parameters for prescription extraction."""
        system_prompt = self.get_system_prompt(
            prescription_schema,
            self.thinking,
            self.transcribe,
            self.medications,
            self.glossary,
        )
        messages = []

        return self.prepare_base_conversation(image, messages, system_prompt, ocr_transcription, response_prefill)

    @retry_bedrock_errors
    def extract_prescription_data(
            self,
            image: "ContentBlockTypeDef",
            prescription_schema: dict[str, Any],
            ocr_transcription: Optional[str] = None,
    ) -> ExtractPrescriptionResult:
        """Extract data from a prescription image."""
        if self.config["transcribe"]:
            response_prefill = "<transcription>"
        elif self.config["thinking"] and "anthropic.claude-3-7-sonnet" not in self.model_id:
            response_prefill = "<thinking>"
        elif not self.config["thinking"]:
            response_prefill = "<isprescription>"
        else:
            response_prefill = ""

        input_params = self.prepare_extract_conversation(
            image=image,
            prescription_schema=prescription_schema,
            ocr_transcription=ocr_transcription,
            response_prefill=response_prefill,
        )

        response = invoke_model_with_input(
            self.bedrock_client,
            **input_params,
        )
        text = build_full_response(response, response_prefill)

        try:
            is_prescription = get_is_prescription(text)
            if not is_prescription:
                logger.debug(f"Not a prescription: {text}")
                raise InvalidImageContentsError("Not a prescription")
            is_handwritten = get_is_handwritten(text)
            prescription_data = get_prescription_data(text)
        except ValueError as e:
            logger.debug(f"Failed to parse output: {text}")
            raise ModelResponseError("Failed to parse output") from e
        try:
            jsonschema.validate(prescription_data, prescription_schema)
        except (json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
            logger.debug(f"Failed to validate output: {json.dumps(prescription_data)}")
            raise ModelResponseError("Failed to validate output") from e
        logger.debug(text)

        return ExtractPrescriptionResult(
            extraction=prescription_data,
            isHandwritten=is_handwritten,
            isPrescription=is_prescription,
            usage=ModelUsage(
                inputTokens=response["usage"]["inputTokens"] + response["usage"].get("cacheWriteInputTokens", 0),
                outputTokens=response["usage"]["outputTokens"],
                cacheReadInputTokens=response["usage"].get("cacheReadInputTokens", 0),
                task=self.task,
            ),
        )
