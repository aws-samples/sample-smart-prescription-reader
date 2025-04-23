# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

"""Module for preparing and making calls to the Bedrock Converse API."""

import logging
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.type_defs import (
        ContentBlockTypeDef,
    )
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)


def get_image_bytes_and_content_type(s3_client: "S3Client", bucket: str, key: str) -> tuple[bytes, str]:
    response = s3_client.get_object(Bucket=bucket, Key=key)
    image_bytes = response["Body"].read()
    content_type = response["ContentType"]
    return image_bytes, content_type


def get_image_for_converse(image: bytes, content_type: str) -> "ContentBlockTypeDef":
    type_suffix = content_type.split("/")[-1]
    if type_suffix in ["gif", "jpeg", "png", "webp"]:
        image_format: Literal["gif", "jpeg", "png", "webp"] = type_suffix  # type: ignore

        return {
            "image": {
                "format": image_format,
                "source": {"bytes": image},
            }
        }
    elif type_suffix in ["pdf"]:
        return {
            "document": {
                "format": "pdf",
                "name": "scanned prescription",
                "source": {"bytes": image},
            }
        }
    else:
        raise ValueError(f"Unsupported image format: {type_suffix}")


def get_medications(s3_client: "S3Client", bucket: str, key: str) -> str:
    if not hasattr(get_medications, "_medications_cache"):
        response = s3_client.get_object(Bucket=bucket, Key=key)
        get_medications._medications_cache = response["Body"].read().decode("utf-8")
        logger.info("Downloaded medications from S3")
    return get_medications._medications_cache


def get_glossary(s3_client: "S3Client", bucket: str, key: str) -> str:
    if not hasattr(get_glossary, "_glossary_cache"):
        response = s3_client.get_object(Bucket=bucket, Key=key)
        get_glossary._glossary_cache = response["Body"].read().decode("utf-8")
        logger.info("Downloaded glossary from S3")
    return get_glossary._glossary_cache
