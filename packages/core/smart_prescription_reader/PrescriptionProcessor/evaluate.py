# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import logging
from typing import TYPE_CHECKING, Any, Optional

from smart_prescription_reader.bedrock_runtime_client import (
    build_full_response,
    invoke_model_with_input,
    retry_bedrock_errors,
)
from smart_prescription_reader.models import ModelUsage
from smart_prescription_reader.models.workflow import (
    EvaluateResponseResult,
    ExtractionQuality,
)
from smart_prescription_reader.PrescriptionProcessor.processor import (
    PrescriptionProcessor,
)
from smart_prescription_reader.utils import extract_tag_value

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.type_defs import ContentBlockTypeDef

logger = logging.getLogger(__name__)


def get_feedback(text: str) -> str:
    """
    Find the value between '<feedback>' tags.

    Args:
        text: String containing XML-style tags with feedback

    Returns:
        str: Feedback string
    """
    value = extract_tag_value(text, "feedback")
    return value


def get_score(text: str) -> ExtractionQuality:
    """
    Find the value between '<rating>' tags.

    Args:
        text: String containing XML-style tags with score

    Returns:
        ExtractionQuality: Score enum
    """
    value = extract_tag_value(text, "rating")
    return ExtractionQuality(value.lower())


class EvaluateResponse(PrescriptionProcessor):
    """Class for handling prescription evaluation operations."""

    task = "JUDGE"

    def prepare_evaluate_conversation(
            self,
            image: "ContentBlockTypeDef",
            prescription_schema: dict[str, Any],
            extraction: str,
            ocr_transcription: Optional[str] = None,
            response_prefill: Optional[str] = None,
    ) -> dict[str, Any]:
        """Prepare the conversation parameters for extraction evaluation."""
        if extraction == "":
            raise ValueError("Extraction must not be empty")
        system_prompt = self.get_evaluation_system_prompt()
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": f"""##Extracted Data##
{extraction}"""
                    },
                ],
            }
        ]

        return self.prepare_base_conversation(image, messages, system_prompt, ocr_transcription, response_prefill)

    @retry_bedrock_errors
    def evaluate_response(
            self,
            image: "ContentBlockTypeDef",
            prescription_schema: dict[str, Any],
            extraction: str,
            ocr_transcription: Optional[str] = None,
    ) -> EvaluateResponseResult:
        """Evaluate an extraction response."""

        if self.config["thinking"] and "anthropic.claude-3-7-sonnet" not in self.model_id:
            response_prefill = "<thinking>"
        elif not self.config["thinking"]:
            response_prefill = "<feedback>"
        else:
            response_prefill = ""

        input_params = self.prepare_evaluate_conversation(
            image=image,
            prescription_schema=prescription_schema,
            extraction=extraction,
            ocr_transcription=ocr_transcription,
        )

        response = invoke_model_with_input(
            self.bedrock_client,
            **input_params,
        )
        text = build_full_response(response, response_prefill)

        try:
            result = EvaluateResponseResult(
                score=get_score(text),
                feedback=get_feedback(text),
                usage=ModelUsage(
                    inputTokens=response["usage"]["inputTokens"] + response["usage"].get("cacheWriteInputTokens", 0),
                    outputTokens=response["usage"]["outputTokens"],
                    cacheReadInputTokens=response["usage"].get("cacheReadInputTokens", 0),
                    task=self.task,
                ),
            )
        except ValueError as e:
            raise ValueError("Failed to parse output") from e

        return result

    def get_evaluation_system_prompt(self) -> str:
        """Get the system prompt for evaluation."""
        template = self.template_env.get_template("evaluate_extraction.jinja2")
        return template.render(  # nosemgrep: direct-use-of-jinja2
            thinking=self.thinking,
            transcribe=self.transcribe,
            medications=self.medications,
            glossary=self.glossary,
        )
