"""
Tests for the OCR service
"""

import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from smart_prescription_reader.models.workflow import OcrInput, OcrResult
from smart_prescription_reader.ocr_service import OcrService

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@pytest.fixture
def mock_textract_response():
    with open(os.path.join(os.path.dirname(__file__), "textract_output.json")) as f:
        return json.loads(f.read())


@pytest.fixture
def mock_textract_client():
    with patch("boto3.client") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_s3_bucket():
    return "imagesBucket"


def test_process_image_success(mock_textract_client, mock_textract_response, mock_s3_bucket):
    # Arrange
    mock_textract_client.detect_document_text.return_value = mock_textract_response
    service = OcrService(mock_textract_client)
    input_data = OcrInput(image="test-image.jpg")

    # Act
    result = service.process_image(mock_s3_bucket, input_data.image)

    # Assert
    assert isinstance(result, OcrResult)
    expected_text = (
        "LIC # 976269\n"
        "MEDICAL CENTRE\n"
        "824 14th Street\n"
        "New York, NY 91743, USA\n"
        "NAME John Smith\n"
        "AGE\n"
        "34\n"
        "ADDRESS 162 Example St, NY\n"
        "DATE 09-11-12\n"
        "RX\n"
        "Betaloc 100mg - / tab BID\n"
        "Dorzolamidum 10 mg - / tab BID\n"
        "Cimetidine 50 mg - 2 tabs TID\n"
        "Oxprelol 50mg - - / tab QD\n"
        "Dr. Steve Johnson\n"
        "signature\n"
        "LABEL\n"
    )
    assert result.transcription == expected_text
    mock_textract_client.detect_document_text.assert_called_once_with(
        Document={"S3Object": {"Bucket": mock_s3_bucket, "Name": "test-image.jpg"}}
    )


def test_process_image_empty_response(mock_textract_client, mock_s3_bucket):
    # Arrange
    mock_textract_client.detect_document_text.return_value = {"Blocks": []}
    service = OcrService(mock_textract_client)
    input_data = OcrInput(image="test-image.jpg")

    # Act
    result = service.process_image(mock_s3_bucket, input_data.image)

    # Assert
    assert isinstance(result, OcrResult)
    assert result.transcription == ""
