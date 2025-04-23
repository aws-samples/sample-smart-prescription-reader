# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from smart_prescription_reader.JobStatus.base import JobStatusRepository
from smart_prescription_reader.models import PrescriptionJob
from smart_prescription_reader.models.workflow import UpdatePrescriptionJobInput


class LocalJobStatusRepository(JobStatusRepository):
    """Local in memory repository implementation for development and testing."""

    def __init__(self):
        self.jobs: dict[str, PrescriptionJob] = {}

    def get_job(self, job_id: str) -> Optional[PrescriptionJob]:
        if job_id not in self.jobs:
            return None
        return self.jobs[job_id]

    def save_job(self, job: dict) -> PrescriptionJob:
        now = datetime.now(timezone.utc)
        job["createdAt"] = now
        job["updatedAt"] = now
        job["ttl"] = int((now + timedelta(hours=24)).timestamp())  # TTL timestamp for deletion in unix epoch seconds

        # Generate and add job ID if not present
        if "jobId" not in job:
            job["jobId"] = str(uuid.uuid4())

        validated = PrescriptionJob.model_validate(job)
        self.jobs[validated.job_id] = validated

        return validated

    def update_job(self, updates: UpdatePrescriptionJobInput) -> None:
        job = self.get_job(updates.job_id)
        if job is None:
            raise ValueError(f"Job {updates.job_id} not found")

        now = datetime.now(timezone.utc)
        job.updated_at = now
        job.ttl = int((now + timedelta(hours=24)).timestamp())  # TTL timestamp for deletion
        for key, value in updates.model_dump().items():
            setattr(job, key, value)

        self.jobs[updates.job_id] = job
