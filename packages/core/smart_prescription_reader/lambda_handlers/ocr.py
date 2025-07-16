"""
Lambda handler for OCR processing using Textract
"""

import logging
import os
from typing import Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.utils import copy_config_to_registered_loggers
from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext

from smart_prescription_reader.models.workflow import OcrInput
from smart_prescription_reader.ocr_service import OcrService
from smart_prescription_reader.utils import get_textract_client

logger = Logger()
external_logger = logging.getLogger()
copy_config_to_registered_loggers(source_logger=logger)
# reducing noise from logs, if you really need DEBUG level logs from these libraries, customize the levels below
logging.getLogger("boto").setLevel(logging.INFO)
logging.getLogger("boto3").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.WARNING)

textract = get_textract_client()


@event_parser(model=OcrInput)
def handler(event: OcrInput, context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for OCR processing

    Args:
        event: Lambda event containing the image information
        context: Lambda context

    Returns:
        Dictionary containing the OCR results
    """
    logger.debug(context)
    logger.debug(event.model_dump_json(by_alias=True))

    INPUT_BUCKET_NAME = os.getenv("INPUT_BUCKET_NAME")

    try:
        # Initialize OCR service
        ocr_service = OcrService(textract)

        # Process image
        result = ocr_service.process_image(INPUT_BUCKET_NAME, event.image)

        # Return result as dict
        return result.model_dump(by_alias=True)

    except Exception as e:
        # Log error and re-raise
        print(f"Error processing OCR request: {str(e)}")
        raise
