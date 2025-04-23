# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import uuid
from datetime import datetime, timedelta, timezone

import pydantic
import pytest

from smart_prescription_reader.JobStatus.local import LocalJobStatusRepository
from smart_prescription_reader.models import PrescriptionJob
from smart_prescription_reader.models.workflow import UpdatePrescriptionJobInput


class TestLocal:
    def test___init___1(self):
        """
        Test that the LocalJobStatusRepository initializes with an empty jobs dictionary.
        """
        repo = LocalJobStatusRepository()
        assert isinstance(repo.jobs, dict)
        assert len(repo.jobs) == 0

    def test___init___no_edge_cases(self):
        """
        This test verifies that the __init__ method of LocalJobStatusRepository
        initializes without any parameters and creates an empty dictionary for jobs.
        There are no explicit edge cases or error conditions handled in the __init__ method.
        """
        repo = LocalJobStatusRepository()
        assert isinstance(repo.jobs, dict)
        assert len(repo.jobs) == 0

    def test_get_job_2(self):
        """
        Test that get_job returns the correct PrescriptionJob when the job_id exists in self.jobs.
        """
        repo = LocalJobStatusRepository()
        job_id = "test_job_id"
        test_job = PrescriptionJob(
            jobId=job_id,
            status="QUEUED",
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            ttl=int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
        )

        repo.jobs[job_id] = test_job

        result = repo.get_job(job_id)

        assert result == test_job
        assert result.job_id == job_id
        assert result.status.value == "QUEUED"

    def test_get_job_nonexistent_id(self):
        """
        Test that get_job returns None when called with a job_id that doesn't exist in the repository.
        """
        repo = LocalJobStatusRepository()
        nonexistent_id = "nonexistent_id"

        result = repo.get_job(nonexistent_id)

        assert result is None, f"Expected None for nonexistent job_id, but got {result}"

    def test_get_job_when_job_id_not_in_jobs(self):
        """
        Test the get_job method when the job_id is not present in the jobs dictionary.

        This test verifies that the get_job method returns None when the provided
        job_id does not exist in the LocalJobStatusRepository's jobs dictionary.
        """
        # Arrange
        repo = LocalJobStatusRepository()
        non_existent_job_id = "non_existent_id"

        # Act
        result = repo.get_job(non_existent_job_id)

        # Assert
        assert result is None

    def test_save_job_2(self):
        """
        Test saving a job with an existing job_id.

        This test verifies that when a job dictionary with a pre-existing job_id
        is passed to the save_job method, it correctly saves the job and returns
        the same job_id without generating a new one.
        """
        repo = LocalJobStatusRepository()
        existing_job_id = "test-job-id"
        job = {
            "jobId": existing_job_id,
            "status": "QUEUED",
        }

        result = repo.save_job(job)

        assert result.job_id == existing_job_id
        assert repo.jobs[existing_job_id].job_id == existing_job_id
        assert repo.jobs[existing_job_id].status.value == "QUEUED"
        assert isinstance(repo.jobs[existing_job_id].created_at, datetime)
        assert isinstance(repo.jobs[existing_job_id].updated_at, datetime)
        assert isinstance(repo.jobs[existing_job_id].ttl, int)

    def test_save_job_missing_required_fields(self):
        """
        Test save_job method with missing required fields in the job dictionary.
        This tests the edge case where the input job dictionary is missing
        fields that are required by the PrescriptionJob model.
        """
        repo = LocalJobStatusRepository()
        job = {}  # Empty dictionary, missing all required fields

        with pytest.raises(pydantic.ValidationError):
            repo.save_job(job)

    def test_save_job_when_job_id_not_present(self):
        """
        Test saving a job without a job_id.

        This test verifies that when a job dictionary without a 'job_id' is passed
        to the save_job method, it generates a new UUID for the job_id, saves the
        job with the generated id, and returns the newly generated job_id.
        """
        repo = LocalJobStatusRepository()
        job = {
            "status": "QUEUED",
        }

        result = repo.save_job(job)

        assert result.job_id is not None
        assert uuid.UUID(result.job_id, version=4)
        saved_job = repo.get_job(result.job_id)
        assert saved_job is not None
        assert saved_job.job_id == result.job_id
        assert saved_job.status == "QUEUED"
        assert isinstance(saved_job.created_at, datetime)
        assert isinstance(saved_job.updated_at, datetime)
        assert isinstance(saved_job.ttl, int)
        assert datetime.fromtimestamp(saved_job.ttl, tz=timezone.utc) > saved_job.updated_at

    def test_update_job_2(self):
        """
        Test updating an existing job in the LocalJobStatusRepository.

        This test verifies that the update_job method correctly updates
        an existing job's attributes when the job is found in the repository.
        It checks that the updatedAt and ttl fields are updated, and that
        the provided updates are applied to the job.
        """
        repo = LocalJobStatusRepository()
        job_id = "test_job_id"
        initial_job = PrescriptionJob(
            jobId=job_id,
            status="QUEUED",
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            ttl=int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
        )

        repo.jobs[job_id] = initial_job

        updates = UpdatePrescriptionJobInput(jobId=job_id, status="COMPLETED")
        repo.update_job(updates)

        updated_job = repo.get_job(job_id)
        assert updated_job is not None
        assert updated_job.status.value == "COMPLETED"
        assert isinstance(updated_job.updated_at, datetime)
        assert isinstance(updated_job.ttl, int)
        assert datetime.fromtimestamp(updated_job.ttl, tz=timezone.utc) > updated_job.updated_at

    def test_update_job_nonexistent_job(self):
        """
        Test updating a job that doesn't exist in the repository.
        This should raise a ValueError with a specific error message.
        """
        repo = LocalJobStatusRepository()
        non_existent_job_id = "non_existent_id"
        updates = UpdatePrescriptionJobInput(jobId=non_existent_job_id, status="COMPLETED")

        with pytest.raises(ValueError, match=f"Job {non_existent_job_id} not found"):
            repo.update_job(updates)
