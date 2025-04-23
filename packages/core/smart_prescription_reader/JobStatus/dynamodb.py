# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from smart_prescription_reader.JobStatus.base import JobStatusRepository
from smart_prescription_reader.models import PrescriptionJob
from smart_prescription_reader.models.workflow import UpdatePrescriptionJobInput

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource


class DynamoDBJobStatusRepository(JobStatusRepository):
    """DynamoDB-based repository implementation."""

    def __init__(self, ddb: "DynamoDBServiceResource", table_name: str):
        self.table = ddb.Table(table_name)

    def get_job(self, job_id: str) -> Optional[PrescriptionJob]:
        response = self.table.get_item(Key={"jobId": job_id})
        item = response.get("Item")
        if not item:
            return None
        return PrescriptionJob.model_validate(item)

    def save_job(self, job: dict) -> PrescriptionJob:
        now = datetime.now(timezone.utc)
        job["createdAt"] = now
        job["updatedAt"] = now
        job["ttl"] = int((now + timedelta(hours=24)).timestamp())  # TTL timestamp for deletion in epoch seconds

        # Generate and add job ID if not present
        if "jobId" not in job:
            job["jobId"] = str(uuid4())

        validated = PrescriptionJob.model_validate(job)
        item = {
            k: v.isoformat() if isinstance(v, datetime) else v
            for k, v in validated.model_dump(by_alias=True, exclude_none=True, exclude_unset=True).items()
        }

        self.table.put_item(Item=item)

        return validated

    def update_job(self, updates: UpdatePrescriptionJobInput) -> None:
        now = datetime.now(timezone.utc)
        updates_dict = updates.model_dump(by_alias=True)
        updates_dict.pop("jobId", None)
        updates_dict["updatedAt"] = now.isoformat()
        updates_dict["ttl"] = int((now + timedelta(hours=24)).timestamp())  # TTL timestamp for deletion

        update_expression = "SET #status = :status, #updatedAt = :updatedAt, #ttl = :ttl"
        expression_attribute_names = {
            "#status": "status",
            "#updatedAt": "updatedAt",
            "#ttl": "ttl",
        }
        expression_attribute_values = {
            ":status": updates_dict["status"],
            ":updatedAt": updates_dict["updatedAt"],
            ":ttl": updates_dict["ttl"],
        }

        # Handle message conditionally
        if updates_dict.get("message"):
            update_expression += ", #message = :message"
            expression_attribute_names["#message"] = "message"
            expression_attribute_values[":message"] = updates_dict["message"]

        # Handle state conditionally
        if updates_dict.get("state"):
            update_expression += ", #state = :state"
            expression_attribute_names["#state"] = "state"
            expression_attribute_values[":state"] = updates_dict["state"]

        # handle prescriptionData conditionally
        if updates_dict.get("prescriptionData"):
            update_expression += ", #prescriptionData = :prescriptionData"
            expression_attribute_names["#prescriptionData"] = "prescriptionData"
            expression_attribute_values[":prescriptionData"] = json.loads(updates_dict["prescriptionData"])

        # Handle score conditionally
        if updates_dict.get("score"):
            update_expression += ", #score = :score"
            expression_attribute_names["#score"] = "score"
            expression_attribute_values[":score"] = updates_dict["score"]

        # Handle usage (as a list)
        if updates_dict.get("usage"):
            update_expression += ", #usage = list_append(if_not_exists(#usage, :emptyList), :usage)"
            expression_attribute_names["#usage"] = "usage"
            expression_attribute_values[":usage"] = [
                {
                    "inputTokens": u["inputTokens"],
                    "outputTokens": u.get("outputTokens"),
                    "cacheReadInputTokens": u.get("cacheReadInputTokens"),
                    "task": u.get("task"),
                }
                for u in updates_dict["usage"]
            ]
            expression_attribute_values[":emptyList"] = []

        # Handle error conditionally
        if updates_dict.get("error"):
            update_expression += ", #error = :error"
            expression_attribute_names["#error"] = "error"
            expression_attribute_values[":error"] = updates_dict["error"]

        #  amazonq-ignore-next-line
        self.table.update_item(
            Key={"jobId": updates.job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
        )
