# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import datetime
import json
from unittest.mock import MagicMock, Mock

from smart_prescription_reader.JobStatus.dynamodb import DynamoDBJobStatusRepository
from smart_prescription_reader.models import (
    ErrorDetail,
    ModelUsage,
    PrescriptionJob,
)
from smart_prescription_reader.models.workflow import UpdatePrescriptionJobInput


class TestDynamodb:
    def test___init___1(self):
        """
        Test the initialization of DynamoDBJobStatusRepository.

        This test verifies that the DynamoDBJobStatusRepository object is correctly
        initialized with the provided DynamoDBServiceResource and table name.
        It checks if the 'table' attribute is set to the correct Table object.
        """
        mock_ddb = Mock()
        mock_table = Mock()
        mock_ddb.Table.return_value = mock_table
        table_name = "test_table"

        repo = DynamoDBJobStatusRepository(mock_ddb, table_name)

        assert repo.table == mock_table
        mock_ddb.Table.assert_called_once_with(table_name)

    def test_get_job_2(self):
        """
        Test that get_job returns a PrescriptionJob when an item is found in the DynamoDB table.

        This test verifies that:
        1. The correct key is used to query the DynamoDB table.
        2. When an item is returned, it is correctly converted to a PrescriptionJob object.
        3. The returned object is an instance of PrescriptionJob.
        """
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "jobId": "test_job_id",
                "status": "COMPLETED",
                "createdAt": "2025-03-23T11:22:33Z",
                "updatedAt": "2025-03-23T11:22:33Z",
                "ttl": 1743000153,
            }
        }

        # Create repository instance with mock table
        repo = DynamoDBJobStatusRepository(Mock(), "test_table")
        repo.table = mock_table

        # Call the method under test
        result = repo.get_job("test_job_id")

        # Verify the result
        assert isinstance(result, PrescriptionJob)
        assert result.job_id == "test_job_id"
        assert result.status.value == "COMPLETED"

        # Verify that get_item was called with the correct key
        mock_table.get_item.assert_called_once_with(Key={"jobId": "test_job_id"})

    def test_get_job_nonexistent_id(self):
        """
        Test the get_job method with a non-existent job ID.
        This tests the edge case where the requested job does not exist in the database.
        """
        mock_ddb = MagicMock()
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table
        mock_table.get_item.return_value = {"Item": None}

        repo = DynamoDBJobStatusRepository(mock_ddb, "test_table")
        result = repo.get_job("non_existent_id")

        assert result is None
        mock_table.get_item.assert_called_once_with(Key={"jobId": "non_existent_id"})

    def test_get_job_when_item_not_found(self):
        """
        Test the get_job method when the item is not found in the DynamoDB table.

        This test verifies that the method returns None when the DynamoDB get_item
        operation returns an empty response (i.e., no item found for the given job_id).
        """
        # Arrange
        mock_ddb = Mock()
        mock_table = Mock()
        mock_ddb.Table.return_value = mock_table
        mock_table.get_item.return_value = {"Item": None}

        repository = DynamoDBJobStatusRepository(mock_ddb, "test-table")

        # Act
        result = repository.get_job("non-existent-job-id")

        # Assert
        assert result is None
        mock_table.get_item.assert_called_once_with(Key={"jobId": "non-existent-job-id"})

    def test_save_job_1(self):
        """
        Test that save_job correctly sets createdAt, updatedAt, and ttl fields,
        and calls put_item with the correct arguments.
        """
        # Mock DynamoDB table
        mock_table = MagicMock()
        repo = DynamoDBJobStatusRepository(MagicMock(), "test_table")
        repo.table = mock_table

        # Create a test job
        job = {
            "status": "QUEUED",
        }

        # Call the method under test
        repo.save_job(job)

        # Assert that put_item was called once
        mock_table.put_item.assert_called_once()

        # Get the Item argument passed to put_item
        saved_item = mock_table.put_item.call_args[1]["Item"]
        print(saved_item)

        # Assert that createdAt, updatedAt, and ttl were set correctly
        assert isinstance(saved_item["createdAt"], str)
        datetime.datetime.fromisoformat(saved_item["createdAt"])
        assert isinstance(saved_item["updatedAt"], str)
        datetime.datetime.fromisoformat(saved_item["updatedAt"])
        assert isinstance(saved_item["ttl"], int)
        datetime.datetime.fromtimestamp(saved_item["ttl"])

    def test_update_job_updates_item_with_correct_parameters(self):
        """
        Test that update_job method calls update_item on the DynamoDB table
        with the correct parameters, including the job_id, updated fields,
        and TTL timestamp.
        """
        # Mock DynamoDB table
        mock_table = MagicMock()
        repository = DynamoDBJobStatusRepository(MagicMock(), "test_table")
        repository.table = mock_table

        # Test data
        job_id = "test_job_id"
        updates = UpdatePrescriptionJobInput(
            jobId=job_id,
            status="PROCESSING",
            state="EXTRACT",
        )

        # Call the method
        repository.update_job(updates)

        # Assert that update_item was called with correct parameters
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]

        assert call_args["Key"] == {"jobId": job_id}
        assert (
                "SET #status = :status, #updatedAt = :updatedAt, #ttl = :ttl, #state = :state"
                in call_args["UpdateExpression"]
        )
        assert call_args["ExpressionAttributeNames"] == {
            "#state": "state",
            "#status": "status",
            "#ttl": "ttl",
            "#updatedAt": "updatedAt",
        }

        # Check that the values are of the correct type
        assert isinstance(call_args["ExpressionAttributeValues"][":status"], str)
        assert isinstance(call_args["ExpressionAttributeValues"][":updatedAt"], str)
        datetime.datetime.fromisoformat(call_args["ExpressionAttributeValues"][":updatedAt"])
        assert isinstance(call_args["ExpressionAttributeValues"][":ttl"], int)
        datetime.datetime.fromtimestamp(call_args["ExpressionAttributeValues"][":ttl"])

    def test_update_job_updates_item_with_error(self):
        # Mock DynamoDB table
        mock_table = MagicMock()
        repository = DynamoDBJobStatusRepository(MagicMock(), "test_table")
        repository.table = mock_table

        # Test data
        job_id = "test_job_id"
        updates = UpdatePrescriptionJobInput(
            jobId=job_id,
            status="FAILED",
            state="EXTRACT",
            error=ErrorDetail(code="ERROR_CODE", message="Error message"),
        )

        # Call the method
        repository.update_job(updates)

        # Assert that update_item was called with correct parameters
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]

        assert call_args["Key"] == {"jobId": job_id}
        assert (
                "SET #status = :status, #updatedAt = :updatedAt, #ttl = :ttl, #state = :state, #error = :error"
                in call_args["UpdateExpression"]
        )
        assert call_args["ExpressionAttributeNames"] == {
            "#state": "state",
            "#status": "status",
            "#ttl": "ttl",
            "#updatedAt": "updatedAt",
            "#error": "error",
        }

        assert call_args["ExpressionAttributeValues"] == {
            ":status": "FAILED",
            ":updatedAt": call_args["ExpressionAttributeValues"][":updatedAt"],
            ":ttl": call_args["ExpressionAttributeValues"][":ttl"],
            ":state": "EXTRACT",
            ":error": {
                "code": "ERROR_CODE",
                "message": "Error message",
            },
        }

    def test_update_job_updates_item_completed(self):
        # Mock DynamoDB table
        mock_table = MagicMock()
        repository = DynamoDBJobStatusRepository(MagicMock(), "test_table")
        repository.table = mock_table

        # Test data
        job_id = "test_job_id"
        prescriptionData = '{"test": "data"}'
        updates = UpdatePrescriptionJobInput(
            jobId=job_id,
            status="COMPLETED",
            state="JUDGE",
            score="FAIR",
            prescriptionData=prescriptionData,
            message="Test message",
            usage=[
                ModelUsage(
                    inputTokens=20,
                    outputTokens=10,
                    task="JUDGE",
                )
            ],
        )

        # Call the method
        repository.update_job(updates)

        # Assert that update_item was called with correct parameters
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]

        assert call_args["Key"] == {"jobId": job_id}
        assert (
                "SET #status = :status, #updatedAt = :updatedAt, #ttl = :ttl, #message = :message, #state = :state, "
                "#prescriptionData = :prescriptionData, #score = :score, #usage = list_append(if_not_exists(#usage, "
                ":emptyList), :usage)" in call_args["UpdateExpression"]
        )
        assert call_args["ExpressionAttributeNames"] == {
            "#message": "message",
            "#prescriptionData": "prescriptionData",
            "#score": "score",
            "#state": "state",
            "#status": "status",
            "#ttl": "ttl",
            "#updatedAt": "updatedAt",
            "#usage": "usage",
        }

        assert call_args["ExpressionAttributeValues"] == {
            ":status": "COMPLETED",
            ":updatedAt": call_args["ExpressionAttributeValues"][":updatedAt"],
            ":ttl": call_args["ExpressionAttributeValues"][":ttl"],
            ":state": "JUDGE",
            ":message": "Test message",
            ":prescriptionData": json.loads(prescriptionData),
            ":score": "FAIR",
            ":usage": [
                {
                    "inputTokens": 20,
                    "outputTokens": 10,
                    "cacheReadInputTokens": None,
                    "task": "JUDGE",
                }
            ],
            ":emptyList": [],
        }
