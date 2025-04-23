# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from smart_prescription_reader.models import (
    PresignedUrlResponse,
    RequestUploadFileInput,
)
from smart_prescription_reader.upload_file import upload_file
from smart_prescription_reader.utils import get_s3_client

logger = Logger()
app = AppSyncResolver()

INPUT_BUCKET_NAME = os.getenv("INPUT_BUCKET_NAME")

s3 = get_s3_client()


@app.resolver(type_name="Mutation", field_name="requestUploadFile")
def request_upload_file(input: dict) -> PresignedUrlResponse:
    username = app.current_event.get("identity", {}).get("username")
    request = RequestUploadFileInput(**input)
    return upload_file(
        s3_client=s3,
        input_bucket=INPUT_BUCKET_NAME,
        file_name=request.file_name,
        expiration=request.expiration,
        username=username,
    ).model_dump(by_alias=True)


def handler(event: dict, context: "LambdaContext") -> dict:
    return app.resolve(event, context)
