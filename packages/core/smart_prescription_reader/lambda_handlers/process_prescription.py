# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from smart_prescription_reader.JobStatus.base import JobStatusRepository
from smart_prescription_reader.JobStatus.dynamodb import DynamoDBJobStatusRepository
from smart_prescription_reader.models import (
    PrescriptionJob,
    ProcessPrescriptionInput,
)
from smart_prescription_reader.utils import (
    get_dynamodb_resource,
    get_step_functions_client,
)

if TYPE_CHECKING:
    from mypy_boto3_stepfunctions import SFNClient

logger = Logger()
app = AppSyncResolver()

JOBS_TABLE = os.getenv("JOBS_TABLE")
PRESCRIPTION_MACHINE = os.getenv("PRESCRIPTION_MACHINE")

dynamodb_client = get_dynamodb_resource()
sfn_client = get_step_functions_client()


class InternalError(Exception):
    def __init__(self, message="Internal error"):
        self.message = message
        super().__init__(self.message)


class UnauthorizedException(Exception):
    """Exception raised for unauthorized access attempts."""

    def __init__(self, message="Unauthorized"):
        self.message = message
        super().__init__(self.message)


def process_prescription(
        sfn: "SFNClient",
        payload: ProcessPrescriptionInput,
        username: str,
        job_status_repo: JobStatusRepository,
) -> PrescriptionJob:
    prescription_job = job_status_repo.save_job({"status": "QUEUED", "owner": username})

    prescription_input = payload.model_dump(by_alias=True)
    prescription_input["jobId"] = prescription_job.job_id

    try:
        sfn.start_execution(
            stateMachineArn=PRESCRIPTION_MACHINE,
            input=json.dumps(prescription_input),
        )
        return prescription_job
    except Exception as e:
        logger.exception("An error occurred during execution", e, stack_info=True, exc_info=True)
        raise InternalError from e


@app.resolver(type_name="Mutation", field_name="processPrescription")
def process_prescription_handler(input: dict) -> dict:
    username = app.current_event.get("identity", {}).get("username")
    if not username:
        raise UnauthorizedException

    try:
        payload = ProcessPrescriptionInput.model_validate(input)
    except Exception as e:
        logger.exception("Invalid input", e)
        raise InternalError from e

    job_status_repo = DynamoDBJobStatusRepository(ddb=dynamodb_client, table_name=JOBS_TABLE)

    prescription_job = process_prescription(
        sfn_client,
        payload,
        username,
        job_status_repo,
    )

    return {
        k: v.isoformat() if isinstance(v, datetime) else v
        for k, v in prescription_job.model_dump(by_alias=True).items()
    }


def handler(event: dict, context: "LambdaContext") -> dict:
    if not JOBS_TABLE:
        logger.error("JOBS_TABLE not set")
        raise InternalError
    if not PRESCRIPTION_MACHINE:
        logger.error("PRESCRIPTION_MACHINE not set")
        raise InternalError
    return app.resolve(event, context)
