# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.


import logging
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import NAMESPACE_X500, uuid4, uuid5

from smart_prescription_reader.models import (
    PresignedUrlResponse,
)
from smart_prescription_reader.utils import create_presigned_url

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)


def create_object_key(file_name: str, username: str = None):
    logger.debug(f"using username for prefix: {username}")

    # we need a unique part since file_names can repeat
    if username:
        # abusing the X500 namespace for a consistent username-based hash in UUID form
        return f"uploads/{str(uuid5(NAMESPACE_X500, username))}-{file_name}"
    else:
        logger.warning("no username found. falling back to a random uuid")
        return f"uploads/{str(uuid4())}-{file_name}"


def upload_file(
        s3_client: "S3Client",
        file_name: str,
        input_bucket: str,
        expiration: int = None,
        username: str = None,
) -> PresignedUrlResponse:
    object_key = create_object_key(file_name, username)

    file_extension = Path(file_name).suffix.lstrip(".")

    # we currently know how to handle zip, csv or some image types
    if file_extension.lower() in ["jpeg", "jpg", "png", "webp", "gif"]:
        if file_extension.lower() == "jpg":
            file_extension = "jpeg"
        content_type = "image/" + file_extension
    elif file_extension.lower() == "zip":
        content_type = "application/zip"
    elif file_extension.lower() == "csv":
        content_type = "text/csv"
    else:
        logger.error("Unsupported file type")
        raise ValueError("Unsupported file type")

    presigned_upload_link = create_presigned_url(
        s3_client,
        logger,
        input_bucket,
        object_key=object_key,
        expiration=expiration,
        client_method="put_object",
        content_type=content_type,
    )

    return PresignedUrlResponse(url=presigned_upload_link, objectKey=object_key)
