# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import logging
import os

import botocore.session
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.utils import copy_config_to_registered_loggers
from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext

from smart_prescription_reader.JobStatus.dynamodb import DynamoDBJobStatusRepository
from smart_prescription_reader.models.workflow import UpdateJobStatusInput
from smart_prescription_reader.update_job_status import prepare_update_job
from smart_prescription_reader.utils import get_dynamodb_resource

logger = Logger()
external_logger = logging.getLogger()
copy_config_to_registered_loggers(source_logger=logger)
# reducing noise from logs, if you really need DEBUG level logs from these libraries, customize the levels below
logging.getLogger("boto").setLevel(logging.INFO)
logging.getLogger("boto3").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.WARNING)

JOB_STATUS_TABLE = os.environ.get("JOB_STATUS_TABLE")
if not JOB_STATUS_TABLE:
    raise ValueError("JOB_STATUS_TABLE environment variable set")
AWS_REGION = os.environ.get("AWS_REGION")
if not AWS_REGION:
    raise ValueError("AWS_REGION environment variable not set")

session = botocore.session.Session()
ddb = get_dynamodb_resource()


@event_parser(model=UpdateJobStatusInput)
def handler(event: UpdateJobStatusInput, context: LambdaContext):
    logger.debug(context)
    logger.debug(event.model_dump_json(by_alias=True))

    if JOB_STATUS_TABLE:
        repo = DynamoDBJobStatusRepository(ddb, JOB_STATUS_TABLE)
    else:
        raise ValueError("No repository configured")

    updates = prepare_update_job(event)

    repo.update_job(updates)

    return {"status": "ok"}
