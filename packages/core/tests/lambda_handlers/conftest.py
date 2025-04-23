# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import os

import pytest


@pytest.fixture
def schema() -> dict:
    return {
        "type": "object",
        "required": ["prescriber", "patient", "date", "medications"],
        "properties": {
            "prescriber": {"type": "string", "description": "Doctor's name"},
            "patient": {"type": "string", "description": "Patient's name"},
            "date": {"type": "string", "description": "Prescription date"},
            "medications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "medication": {
                            "type": "string",
                            "description": "Name of the medication",
                        },
                        "dosage": {
                            "type": "string",
                            "description": "Prescribed dosage",
                        },
                        "frequency": {
                            "type": "string",
                            "description": "How often to take the medication",
                        },
                    },
                },
            },
        },
    }


@pytest.fixture(scope="class")
def image_key() -> str:
    key = "test/prescription.jpeg"

    return key


def image_bytes_and_content_type(*args, **kwargs) -> tuple[bytes, str]:
    return open(os.path.join(os.path.dirname(__file__), "prescription.jpeg"), "rb").read(), "image/jpeg"


@pytest.fixture
def mock_get_image_bytes_and_content_type(*args, **kwargs):
    return image_bytes_and_content_type


@pytest.fixture
def extraction():
    return {
        "prescriber": "Dr. Steve Johnson",
        "patient": "John Smith",
        "date": "09-11-12",
        "medications": [
            {
                "medication": "Betaloc",
                "dosage": "100mg - 1 tab",
                "frequency": "BID",
            },
            {
                "medication": "Dorzolamid",
                "dosage": "10mg - 1 tab",
                "frequency": "BID",
            },
            {
                "medication": "Cimetidine",
                "dosage": "50mg - 2 tabs",
                "frequency": "TID",
            },
            {
                "medication": "Oxprelol",
                "dosage": "50mg - 1 tab",
                "frequency": "QD",
            },
        ],
    }


@pytest.fixture
def feedback():
    return """Field-by-field analysis:
Prescriber:
- Legible in image
- Correct transcription: "Dr. Steve Johnson"
Patient:
- Legible in image
- Correct transcription: "John Smith"
Date:
- Legible in image
- Correct transcription: "09-11-12"
Medications:
1. First medication:
   - Legible in image
   - Correct transcription of medication name, dosage and frequency
2. Second medication:
   - Legible in image
   - Incorrect transcription of medication name
   - The medication is clearly written as "Dorzolamidum" in the image, but extracted as "Dorzolamid"
   - Recommended correction: Change "Dorzolamid" to "Dorzolamidum"
3. Third medication:
   - Legible in image
   - Correct transcription of medication name, dosage and frequency
   - Minor spacing difference between image (50 mg) and extraction (50mg), but this is not clinically significant
4. Fourth medication:
   - Legible in image
   - Correct transcription of medication name, dosage and frequency
Common Issues:
- The only significant error is in the second medication name
- Truncation/misspelling of medication names could lead to dispensing errors
- Otherwise, the extraction is highly accurate with proper preservation of dosing information"""
