"""
OCR service implementation using Amazon Textract
"""

from typing import TYPE_CHECKING

from smart_prescription_reader.models.workflow import OcrResult
from smart_prescription_reader.textract_helper import get_paragraphs

if TYPE_CHECKING:
    from mypy_boto3_textract import TextractClient


class OcrService:
    """Service class for performing OCR using Amazon Textract"""

    def __init__(self, textract: "TextractClient"):
        self.textract_client = textract

    def process_image(self, bucket: str, key: str) -> OcrResult:
        """
        Process an image using Amazon Textract to extract text

        Args:
            bucket: str, S3 bucket name containing the image
            key: str, S3 key of the image

        Returns:
            OcrResult object containing the extracted text
        """

        # Call Textract to get document text
        response = self.textract_client.detect_document_text(Document={"S3Object": {"Bucket": bucket, "Name": key}})

        transcription = get_paragraphs(response)

        return OcrResult(transcription=transcription)
