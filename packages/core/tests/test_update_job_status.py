# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json

from smart_prescription_reader.models.workflow import UpdateJobStatusInput, UpdatePrescriptionJobInput
from smart_prescription_reader.update_job_status import prepare_update_job


class TestUpdateJobStatus:
    def test_prepare_update_job_with_none_prescription_data(self):
        """
        Test prepare_update_job when prescription_data is None.
        This tests the explicit handling of None prescription_data in the focal method.
        """
        input_event = UpdateJobStatusInput(
            jobId="test_job_id",
            status="COMPLETED",
            state="CORRECT",
            message="Job completed successfully",
            usage=[{"task": "CORRECT", "inputTokens": 550, "outputTokens": 20}],
            prescriptionData=None,
            error=None,
        )

        result = prepare_update_job(input_event)

        assert isinstance(result, UpdatePrescriptionJobInput)
        assert result.job_id == "test_job_id"
        assert result.status.value == "COMPLETED"
        assert result.state.value == "CORRECT"
        assert result.message == "Job completed successfully"
        assert result.usage[0].task == "CORRECT"
        assert result.usage[0].input_tokens == 550
        assert result.usage[0].output_tokens == 20
        assert result.prescription_data is None
        assert result.error is None

    def test_prepare_update_job_with_prescription_data(self):
        """
        Test prepare_update_job function when prescription_data is provided.
        Verifies that the function correctly transforms UpdateJobStatusInput
        into UpdatePrescriptionJobInput, including JSON encoding of prescription_data.
        """
        input_event = UpdateJobStatusInput(
            jobId="test_job_id",
            status="COMPLETED",
            state="CORRECT",
            message="Job completed successfully",
            usage=[{"task": "CORRECT", "inputTokens": 550, "outputTokens": 20}],
            prescriptionData={"key": "value"},
            error=None,
        )

        result = prepare_update_job(input_event)

        assert isinstance(result, UpdatePrescriptionJobInput)
        assert result.job_id == "test_job_id"
        assert result.status.value == "COMPLETED"
        assert result.state.value == "CORRECT"
        assert result.message == "Job completed successfully"
        assert result.usage[0].task == "CORRECT"
        assert result.usage[0].input_tokens == 550
        assert result.usage[0].output_tokens == 20
        assert result.prescription_data == json.dumps({"key": "value"})
        assert result.error is None

    def test_prepare_update_job_with_error(self):
        """
        Test prepare_update_job function when error is provided.
        Verifies that the function correctly transforms UpdateJobStatusInput
        into UpdatePrescriptionJobInput, including JSON encoding of error.
        """
        input_event = UpdateJobStatusInput(
            jobId="test_job_id",
            status="FAILED",
            state="EXTRACT",
            message="Job failed due to incorrect input",
            usage=[{"task": "EXTRACT", "inputTokens": 550, "outputTokens": 20}],
            prescriptionData=None,
            error={"code": "INVALID_INPUT", "message": "Invalid input provided"},
        )

        result = prepare_update_job(input_event)

        assert isinstance(result, UpdatePrescriptionJobInput)
        assert result.job_id == "test_job_id"
        assert result.status.value == "FAILED"
        assert result.state.value == "EXTRACT"
        assert result.message == "Job failed due to incorrect input"
        assert result.usage[0].task == "EXTRACT"
        assert result.usage[0].input_tokens == 550
        assert result.usage[0].output_tokens == 20
        assert result.prescription_data is None
        assert result.error.code == "INVALID_INPUT"
        assert result.error.message == "Invalid input provided"

    def test_prepare_update_job_with_missing_optional_fields(self):
        """
        Test prepare_update_job function when optional fields are missing.
        Verifies that the function correctly handles the absence of optional fields.
        """
        input_event = UpdateJobStatusInput(
            jobId="test_job_id",
            status="COMPLETED",
            message="Job completed successfully",
            usage=[{"task": "CORRECT", "inputTokens": 550, "outputTokens": 20}],
        )

        result = prepare_update_job(input_event)

        assert isinstance(result, UpdatePrescriptionJobInput)
        assert result.job_id == "test_job_id"
        assert result.status.value == "COMPLETED"
        assert result.message == "Job completed successfully"
        assert result.prescription_data is None
        assert result.error is None
