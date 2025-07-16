# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json

import pytest

from smart_prescription_reader.models.workflow import EvaluateResponseResult


@pytest.mark.usefixtures("integration_env")
@pytest.mark.integration
class TestEvaluateResponseIntegration:
    def test_evaluate_response(
        self,
        monkeypatch,
        mock_get_image_bytes_and_content_type,
        schema,
        image_key,
        extraction,
    ):
        monkeypatch.setattr(
            "smart_prescription_reader.lambda_handlers.evaluate_response.get_image_bytes_and_content_type",
            mock_get_image_bytes_and_content_type,
        )
        from smart_prescription_reader.lambda_handlers import evaluate_response

        response = evaluate_response.handler(
            {
                "prescriptionSchema": json.dumps(schema),
                "image": image_key,
                "extraction": extraction,
            },
            {},
        )

        result = EvaluateResponseResult.model_validate(response)
        print(result.model_dump_json(indent=2))

        serialized_result = json.dumps(response)
        assert serialized_result is not None
        assert response["score"] in ["poor", "fair", "good", "excellent"]
        assert len(response["feedback"]) > 0
        assert response["usage"]["inputTokens"] > 0
        assert response["usage"]["outputTokens"] > 0
