# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

"""Module containing prescription processing classes for handling different prescription operations."""

import logging
from typing import TYPE_CHECKING, Any, Optional, TypedDict

import jinja2

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient
    from mypy_boto3_bedrock_runtime.type_defs import ContentBlockTypeDef

logger = logging.getLogger(__name__)


class PrescriptionProcessor:
    """Base class for processing prescriptions with shared functionality."""

    def __init__(
            self,
            bedrock_client: "BedrockRuntimeClient",
            template_env: jinja2.Environment,
            model_id: str,
            temperature: Optional[float] = None,
            medications: Optional[str] = None,
            glossary: Optional[str] = None,
            thinking: bool = False,
            transcribe: bool = False,
            prompt_cache: bool = False,
    ):
        """Initialize the PrescriptionProcessor with shared configuration.

        Args:
            bedrock_client: Bedrock runtime client for making API calls
            template_env: Jinja2 environment for template processing
            model_id: ID of the model to use
            temperature: Temperature parameter for model inference
            medications: Optional medications list
            glossary: Optional glossary
            thinking: Whether to include thinking steps in output
            transcribe: Whether to include transcription in output
        """
        self.bedrock_client = bedrock_client
        self.template_env = template_env
        self.model_id = model_id
        self.temperature = temperature if temperature else 0.0
        self.thinking = thinking
        self.transcribe = transcribe
        self.medications = medications
        self.glossary = glossary
        self.config: ConversationConfig = {
            "model_id": model_id,
            "temperature": self.temperature,
            "max_tokens": 2048,
            "thinking": thinking,
            "transcribe": transcribe,
            "prompt_cache": prompt_cache,
        }

    def get_system_prompt(
            self,
            prescription_schema: dict[str, Any],
            thinking: Optional[bool] = None,
            transcribe: Optional[bool] = None,
            medications: Optional[str] = None,
            glossary: Optional[str] = None,
    ) -> str:
        """Get the system prompt for prescription extraction.

        Args:
            prescription_schema: Schema for prescription data
            thinking: Whether to include thinking steps in output (defaults to instance setting)
            transcribe: Whether to include transcription in output (defaults to instance setting)
            medications: Optional medications list (defaults to instance setting)
            glossary: Optional glossary (defaults to instance setting)
        """
        if thinking is None:
            thinking = self.thinking
        if transcribe is None:
            transcribe = self.transcribe
        if medications is None:
            medications = self.medications
        if glossary is None:
            glossary = self.glossary

        template = self.template_env.get_template("extract_prescription.jinja2")
        return template.render(  # nosemgrep: direct-use-of-jinja2
            output_schema=prescription_schema,
            medications=medications,
            thinking=thinking,
            transcribe=transcribe,
            glossary=glossary,
        )

    def prepare_base_conversation(
            self,
            image: "ContentBlockTypeDef",
            messages: list,
            system_prompt: str = None,
            ocr_transcription: Optional[str] = None,
            response_prefill: Optional[str] = None,
    ) -> dict[str, Any]:
        """Prepare the base conversation parameters.

        Args:
            image: Image content block for the conversation
            system_prompt: System prompt for the model
            messages: List of message objects for the conversation
            ocr_transcription: Optional OCR transcription text
        """
        content = [image]
        if ocr_transcription:
            content.append({"text": "## OCR Extracted Text\n\n" + ocr_transcription})

        if self.config["prompt_cache"]:
            content.append({"text": "Please process this image."})
            content.append({"cachePoint": {"type": "default"}})

        temperature = self.config["temperature"]

        additional_fields = None
        if "anthropic.claude-3-7-sonnet" in self.config["model_id"] and self.config["thinking"]:
            additional_fields = {"thinking": {"budget_tokens": 1024, "type": "enabled"}}
            temperature = 1
        elif response_prefill:
            # response prefill is incompatible with extended reasoning, so only enable if  not using extended reasoning
            messages.append({"role": "assistant", "content": [{"text": response_prefill}]})

        system = []
        if system_prompt:
            system.append({"text": system_prompt})
            if self.config.get("prompt_cache"):
                system.append({"cachePoint": {"type": "default"}})

        return {
            "modelId": self.config["model_id"],
            "system": system,
            "messages": [{"role": "user", "content": content}] + messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": self.config["max_tokens"],
            },
            "additionalModelRequestFields": additional_fields,
        }


class ConversationConfig(TypedDict):
    """Configuration for a conversation with the Bedrock Converse API."""

    model_id: str
    temperature: float
    max_tokens: int
    thinking: bool
    transcribe: bool
    prompt_cache: bool
