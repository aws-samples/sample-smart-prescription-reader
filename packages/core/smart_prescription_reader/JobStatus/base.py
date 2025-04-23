# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

from abc import ABC, abstractmethod
from typing import Optional

from smart_prescription_reader.models import PrescriptionJob
from smart_prescription_reader.models.workflow import UpdatePrescriptionJobInput


class JobStatusRepository(ABC):
    """Base class for repository implementations."""

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[PrescriptionJob]:
        """Retrieve a job by its ID."""
        pass

    @abstractmethod
    def save_job(self, job: dict) -> PrescriptionJob:
        """Save a job. Return the ID."""
        pass

    @abstractmethod
    def update_job(self, updates: UpdatePrescriptionJobInput) -> None:
        """Update specific fields of a job."""
        pass
