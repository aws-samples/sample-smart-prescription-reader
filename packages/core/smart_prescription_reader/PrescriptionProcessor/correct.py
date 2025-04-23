# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

import jsonschema

from smart_prescription_reader.bedrock_runtime_client import (
    build_full_response,
    invoke_model_with_input,
    retry_bedrock_errors,
)
from smart_prescription_reader.exceptions import ModelResponseError
from smart_prescription_reader.models import ModelUsage
from smart_prescription_reader.models.workflow import CorrectResponseResult
from smart_prescription_reader.PrescriptionProcessor.extract import (
    get_prescription_data,
)
from smart_prescription_reader.PrescriptionProcessor.processor import (
    PrescriptionProcessor,
)

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.type_defs import ContentBlockTypeDef, MessageTypeDef

logger = logging.getLogger(__name__)


class CorrectResponse(PrescriptionProcessor):
    """Class for handling prescription correction operations."""

    task = "CORRECT"

    def prepare_correction_conversation(
            self,
            image: "ContentBlockTypeDef",
            prescription_schema: dict[str, Any],
            extraction: str,
            feedback: str,
            response_prefill: Optional[str] = None,
            ocr_transcription: Optional[str] = None,
    ) -> dict[str, Any]:
        """Prepare the conversation parameters for extraction correction."""
        if feedback == "":
            raise ValueError("Feedback must not be empty")
        if extraction == "":
            raise ValueError("Extraction must not be empty")
        system_prompt = self.get_system_prompt(
            prescription_schema,
            self.thinking,
            self.transcribe,
            self.medications,
            self.glossary,
        )
        template = self.template_env.get_template("corrections.jinja2")
        messages: list[MessageTypeDef] = [
            {
                "role": "assistant",
                "content": [
                    {
                        "text": f"""<prescriptiondata>
{extraction}
</prescriptiondata>"""
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "text": template.render(  # nosemgrep: direct-use-of-jinja2
                            feedback=feedback,
                            repeat_schema=True,
                            output_schema=prescription_schema,
                        ),
                    }
                ],
            },
        ]
        return self.prepare_base_conversation(image, messages, system_prompt, ocr_transcription, response_prefill)

    @retry_bedrock_errors
    def correct_response(
            self,
            image: "ContentBlockTypeDef",
            prescription_schema: dict[str, Any],
            extraction: str,
            feedback: str,
            ocr_transcription: Optional[str] = None,
    ) -> CorrectResponseResult:
        """Correct an extraction based on feedback."""
        if self.config["thinking"] and "anthropic.claude-3-7-sonnet" in self.model_id:
            response_prefill = ""
        else:
            response_prefill = "<prescriptiondata>"

        input_params = self.prepare_correction_conversation(
            image=image,
            prescription_schema=prescription_schema,
            extraction=extraction,
            feedback=feedback,
            response_prefill=response_prefill,
            ocr_transcription=ocr_transcription,
        )

        response = invoke_model_with_input(
            self.bedrock_client,
            **input_params,
        )
        text = build_full_response(response, response_prefill)

        prescription_data = get_prescription_data(text)

        try:
            jsonschema.validate(prescription_data, prescription_schema)
        except (json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
            logger.debug(f"Failed to validate output: {json.dumps(prescription_data)}")
            raise ModelResponseError("Failed to validate output") from e

        return CorrectResponseResult(
            extraction=prescription_data,
            usage=ModelUsage(
                inputTokens=response["usage"]["inputTokens"] + response["usage"].get("cacheWriteInputTokens", 0),
                outputTokens=response["usage"]["outputTokens"],
                cacheReadInputTokens=response["usage"].get("cacheReadInputTokens", 0),
                task=self.task,
            ),
        )
