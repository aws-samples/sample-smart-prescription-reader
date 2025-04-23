# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

# nosemgrep: python37-compatibility-importlib2
import importlib.resources
import json
import logging
import os

import jinja2
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.utils import copy_config_to_registered_loggers
from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext

import smart_prescription_reader
from smart_prescription_reader.models.workflow import EvaluateResponseInput
from smart_prescription_reader.PrescriptionProcessor.config import (
    PrescriptionReaderConfig,
)
from smart_prescription_reader.PrescriptionProcessor.evaluate import EvaluateResponse
from smart_prescription_reader.PrescriptionProcessor.utils import (
    get_glossary,
    get_image_bytes_and_content_type,
    get_image_for_converse,
    get_medications,
)
from smart_prescription_reader.utils import (
    get_bedrock_runtime_client,
    get_s3_client,
    get_ssm_client,
)

logger = Logger()
external_logger = logging.getLogger()
copy_config_to_registered_loggers(source_logger=logger)
# reducing noise from logs, if you really need DEBUG level logs from these libraries, customize the levels below
logging.getLogger("boto").setLevel(logging.INFO)
logging.getLogger("boto3").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.WARNING)

s3 = get_s3_client()
bedrock = get_bedrock_runtime_client()
ssm = get_ssm_client()

INPUT_BUCKET_NAME = os.getenv("INPUT_BUCKET_NAME")
CONFIG_BUCKET_NAME = os.getenv("CONFIG_BUCKET_NAME")
CONFIG_PARAM = os.getenv("CONFIG_PARAM")


@event_parser(model=EvaluateResponseInput)
def handler(event: EvaluateResponseInput, context: LambdaContext) -> dict:
    logger.debug(context)
    logger.debug(event.model_dump_json(by_alias=True))

    config = (
        PrescriptionReaderConfig.model_validate_ssm(ssm, CONFIG_PARAM) if CONFIG_PARAM else PrescriptionReaderConfig()
    )
    logger.debug(config.model_dump_json(by_alias=True))

    medications = get_medications(s3, CONFIG_BUCKET_NAME, config.medications_key) if config.medications_key else None
    glossary = get_glossary(s3, CONFIG_BUCKET_NAME, config.glossary_key) if config.glossary_key else None
    template_env = jinja2.Environment(  # nosemgrep: direct-use-of-jinja2
        loader=jinja2.FileSystemLoader(str(importlib.resources.files(smart_prescription_reader) / "prompts")),
        autoescape=True,
    )
    evaluator = EvaluateResponse(
        bedrock_client=bedrock,
        template_env=template_env,
        model_id=event.model if event.model else config.model_id,
        temperature=event.temperature,
        thinking=config.thinking,
        medications=medications,
        glossary=glossary,
        prompt_cache=config.prompt_cache(event.model),
    )

    image, content_type = get_image_bytes_and_content_type(s3, INPUT_BUCKET_NAME, event.image)

    image_block = get_image_for_converse(image, content_type)
    result = evaluator.evaluate_response(
        image_block,
        json.loads(event.prescription_schema),
        event.extraction,
        event.ocr_transcription,
    )

    return result.model_dump(by_alias=True)
