# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json

from smart_prescription_reader.models.workflow import (
    UpdateJobStatusInput,
    UpdatePrescriptionJobInput,
)


def prepare_update_job(event: UpdateJobStatusInput) -> UpdatePrescriptionJobInput:
    return UpdatePrescriptionJobInput(
        jobId=event.job_id,
        status=event.status,
        state=event.state,
        message=event.message,
        usage=event.usage,
        prescriptionData=json.dumps(event.prescription_data) if event.prescription_data else None,
        score=event.score,
        error=event.error,
    )
