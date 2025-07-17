# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

import jinja2
import json_repair

from smart_prescription_reader.bedrock_runtime_client import (
    build_full_response,
    retry_bedrock_errors,
)

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

from smart_prescription_reader.drug_name_matcher import DrugNameMatcher
from smart_prescription_reader.exceptions import ModelResponseError
from smart_prescription_reader.models.drug_information import DrugInformation
from smart_prescription_reader.models.drug_repository import DrugInformationRepository
from smart_prescription_reader.PrescriptionProcessor.processor import PrescriptionProcessor


class IdentifyMedications(PrescriptionProcessor):
    """Class for handling medication identification operations.

    This class extends the PrescriptionProcessor to provide medication identification
    capabilities. It uses a drug repository to find matching medications in the
    prescription text and provides context for the extraction model.

    Attributes:
        drug_repository: Repository for accessing drug information
        _drug_matcher: Lazy-loaded matcher for fuzzy matching of drug names
    """

    task = "IDENTIFY"

    def __init__(
        self,
        bedrock_client: "BedrockRuntimeClient",
        template_env: jinja2.Environment,
        config: dict[str, Any],
        drug_repository: Optional[DrugInformationRepository] = None,
    ):
        """Initialize the IdentifyMedications processor.

        Args:
            bedrock_client: Bedrock runtime client for making API calls
            template_env: Jinja2 environment for template processing
            config: Configuration dictionary
            drug_repository: Optional repository for accessing drug information
        """
        # Store the original config for our own use
        self._original_config = config.copy()

        super().__init__(
            bedrock_client=bedrock_client,
            template_env=template_env,
            model_id=config.get("model_id", ""),
            temperature=config.get("temperature"),
            medications=config.get("medications"),
            glossary=config.get("glossary"),
            thinking=config.get("thinking", False),
            transcribe=config.get("transcribe", False),
            prompt_cache=config.get("prompt_cache", False),
        )
        self.drug_repository = drug_repository
        self._drug_matcher = None

    @property
    def drug_matcher(self) -> Optional[DrugNameMatcher]:
        """Lazy-load drug matcher with word list from repository.

        Returns:
            DrugNameMatcher instance or None if repository is not available
        """
        if self._drug_matcher is None and self.drug_repository is not None:
            # Get threshold from original config, default to 70 if not specified
            threshold = int(self._original_config.get("drug_match_threshold", 70))
            try:
                drug_name_list = self.drug_repository.get_drug_name_list()
                if drug_name_list:
                    self._drug_matcher = DrugNameMatcher(word_list=drug_name_list, threshold=threshold)
                    logging.info(
                        f"Initialized DrugNameMatcher with {len(drug_name_list)} drug names and threshold {threshold}"
                    )
                else:
                    logging.warning("Drug name list is empty, DrugNameMatcher not initialized")
            except Exception as e:
                logging.error(f"Failed to initialize DrugNameMatcher: {e}")

        return self._drug_matcher

    def get_identify_system_prompt(
        self,
    ) -> str:
        template = self.template_env.get_template("identify_medications.jinja2")
        return template.render()  # nosemgrep: direct-use-of-jinja2

    def prepare_identify_conversation(self, ocr_transcription: str) -> dict[str, Any]:
        """Prepare the conversation parameters for medication identification."""
        temperature = self.config["temperature"]
        additional_fields = None

        system_prompt = self.get_identify_system_prompt()
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": f"""##Prescription Transcription##
{ocr_transcription}"""
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"text": "["},
                ],
            },
        ]

        system = []
        if system_prompt:
            system.append({"text": system_prompt})
            if self.config.get("prompt_cache"):
                system.append({"cachePoint": {"type": "default"}})

        return {
            "modelId": self.config["model_id"],
            "system": system,
            "messages": messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": self.config["max_tokens"],
                "stopSequences": ["]"],
            },
            "additionalModelRequestFields": additional_fields,
        }

    @retry_bedrock_errors
    def identify_medications(
        self,
        ocr_transcription: str,
    ) -> list[str]:
        """Identify medications in the prescription."""
        input_params = self.prepare_identify_conversation(
            ocr_transcription=ocr_transcription,
        )

        response = self.bedrock_client.invoke_model_with_response_stream(
            **input_params,
        )
        text = build_full_response(response, "[", "]")

        try:
            medications = json_repair.loads(text)
            return medications
        except (json.JSONDecodeError, ValueError) as e:
            logging.debug("Failed to parse output: %s", text)
            raise ModelResponseError("Failed to parse output") from e

    def find_matching_medications(self, ocr_transcription: str, limit_kb: int = 100) -> list[DrugInformation]:
        """Identify medications and find matches in the drug database.

        This method uses the identify_medications method to get potential medication names,
        then uses the DrugNameMatcher to find fuzzy matches, and finally uses the
        DrugInformationRepository to get medication details.

        Args:
            ocr_transcription: OCR transcription text
            limit_kb: Maximum size of results in KB

        Returns:
            List of DrugInformation objects matching the identified medications
        """
        # If we don't have a drug repository, return empty list
        if not self.drug_repository:
            logging.warning("Drug repository not available, cannot find matching medications")
            return []

        # Identify potential medication names
        try:
            potential_medications = self.identify_medications(ocr_transcription)
            if not potential_medications:
                logging.info("No potential medications identified in OCR text")
                return []

            logging.info(f"Identified {len(potential_medications)} potential medications: {potential_medications}")

            # Find fuzzy matches if we have a drug matcher
            if self.drug_matcher:
                matched_names = self.drug_matcher.list_matches(potential_medications)
                logging.info(f"Found {len(matched_names)} matched medication names")
            else:
                # If no drug matcher, use the potential medications directly
                matched_names = set(potential_medications)

            # If no matches, return empty list
            if not matched_names:
                logging.info("No medication matches found")
                return []

            # Get medication details from repository
            return self.drug_repository.search_drugs(list(matched_names), limit_kb=limit_kb)

        except Exception as e:
            logging.error(f"Error finding matching medications: {e}")
            return []

    def get_medication_context(self, ocr_transcription: str, limit_kb: int = 100) -> str:
        """Generate medication context for extraction prompts.

        This method identifies medications in the OCR text, finds matches in the
        drug database, and formats the information for use in extraction prompts.
        It handles empty results gracefully and relies on the limit_kb parameter
        to control the size of the context.

        Args:
            ocr_transcription: OCR transcription text
            limit_kb: Maximum size of results in KB (default: 100)

        Returns:
            Formatted medication context string or empty string if no medications found
        """
        # Find matching medications
        # The drug repository already handles size limiting based on limit_kb
        medications = self.find_matching_medications(ocr_transcription, limit_kb=limit_kb)

        # If no medications found, return empty string
        if not medications:
            logging.info("No medications found for context generation")
            return ""

        # Format medication information
        context_lines = ["##Medication Information##", "Use this information to help correct transcription errors:"]

        for med in medications:
            # Format: Drug Name (Active Ingredient): Strength Form
            line = f"- {med.drug_name}"

            # Add active ingredient if different from drug name
            if med.active_ingredient and med.active_ingredient != med.drug_name:
                line += f" ({med.active_ingredient})"

            # Add strength and form if available
            if med.strength or med.form:
                line += ": "
                if med.strength:
                    line += med.strength
                if med.form:
                    line += f" {med.form}"

            context_lines.append(line)

        # Join lines into a single string
        context = "\n".join(context_lines)

        logging.info(f"Generated medication context with {len(medications)} medications")
        return context
