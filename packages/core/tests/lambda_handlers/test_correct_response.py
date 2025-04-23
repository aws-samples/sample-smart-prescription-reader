# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json

import jsonschema
import pytest

from smart_prescription_reader.models.workflow import CorrectResponseResult


@pytest.mark.usefixtures("integration_env")
@pytest.mark.integration
class TestCorrectResponseIntegration:
    def test_evaluate_response(
            self,
            monkeypatch,
            mock_get_image_bytes_and_content_type,
            schema,
            image_key,
            extraction,
            feedback,
    ):
        monkeypatch.setattr(
            "smart_prescription_reader.lambda_handlers.correct_response.get_image_bytes_and_content_type",
            mock_get_image_bytes_and_content_type,
        )
        from smart_prescription_reader.lambda_handlers import correct_response

        response = correct_response.handler(
            {
                "prescriptionSchema": json.dumps(schema),
                "image": image_key,
                "extraction": extraction,
                "feedback": feedback,
            },
            {},
        )

        result = CorrectResponseResult.model_validate(response)
        print(result.model_dump_json(indent=2))

        serialized_response = json.dumps(response)
        assert serialized_response is not None

        try:
            jsonschema.validate(response["extraction"], schema)
        except Exception as e:
            assert False, f"Schema validation failed: {e}"
        assert response["usage"]["inputTokens"] > 0
        assert response["usage"]["outputTokens"] > 0
