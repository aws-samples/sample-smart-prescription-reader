# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json

import jsonschema
import pytest

from smart_prescription_reader.models.workflow import ExtractPrescriptionResult


@pytest.mark.usefixtures("integration_env")
@pytest.mark.integration
class TestExtractPrescriptionIntegration:
    def test_extract_prescription(self, monkeypatch, mock_get_image_bytes_and_content_type, schema, image_key):
        monkeypatch.setattr(
            "smart_prescription_reader.lambda_handlers.extract_prescription.get_image_bytes_and_content_type",
            mock_get_image_bytes_and_content_type,
        )
        from smart_prescription_reader.lambda_handlers import extract_prescription

        response = extract_prescription.handler(
            {"prescriptionSchema": json.dumps(schema), "image": image_key},
            {},
        )

        result = ExtractPrescriptionResult.model_validate(response)
        print(result.model_dump_json(indent=2))

        serialized_response = json.dumps(response)
        assert serialized_response is not None

        assert response["isPrescription"]
        try:
            jsonschema.validate(response["extraction"], schema)
        except Exception as e:
            assert False, f"Schema validation failed: {e}"
        assert response["usage"]["inputTokens"] > 0
        assert response["usage"]["outputTokens"] > 0
