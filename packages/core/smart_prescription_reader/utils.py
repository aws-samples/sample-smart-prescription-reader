# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.


import logging
from typing import TYPE_CHECKING, Optional

import botocore.exceptions
from boto3 import Session

from smart_prescription_reader.exceptions import ModelResponseError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
    from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_stepfunctions import SFNClient
    from mypy_boto3_textract import TextractClient


def get_dynamodb_client() -> "DynamoDBClient":
    return Session().client("dynamodb")


def get_dynamodb_resource() -> "DynamoDBServiceResource":
    return Session().resource("dynamodb")


def get_s3_client() -> "S3Client":
    return Session().client("s3")


def get_bedrock_runtime_client() -> "BedrockRuntimeClient":
    return Session().client("bedrock-runtime")


def get_step_functions_client() -> "SFNClient":
    return Session().client("stepfunctions")


def get_ssm_client() -> "SSMClient":
    return Session().client("ssm")


def get_textract_client() -> "TextractClient":
    return Session().client("textract")


def create_presigned_url(
        client: "S3Client",
        logger,
        bucket_name: str,
        object_key: str,
        client_method: str,
        content_type: Optional[str] = None,
        expiration: int = 3600,
):
    """Generate a presigned URL S3 POST request to upload a file

    :param client: boto3 s3 client
    :param logger: logging object
    :param bucket_name: str
    :param object_key: str
    :param client_method: str should be either put_object or get_object
    :param content_type: str Content type to include in Params of call to generate_presigned_url as part of the expected Headers
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    params = {
        "Bucket": bucket_name,
        "Key": object_key,
    }

    if content_type is not None:
        params["ContentType"] = content_type
        params["ServerSideEncryption"] = "AES256"

    try:
        url = client.generate_presigned_url(ClientMethod=client_method, Params=params, ExpiresIn=expiration)
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        raise

    return url


def get_s3_object_bytes_and_type(client: "S3Client", bucket_name: str, object_key: str) -> (bytes, str):
    """Get object from S3 and return the bytes and content type

    :param client: boto3 s3 client
    :param bucket_name: str
    :param object_key: str
    :return: Tuple of bytes and content type
    """
    try:
        response = client.get_object(Bucket=bucket_name, Key=object_key)
        content_type = response["ContentType"]
        object_bytes = response["Body"].read()
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        raise

    return object_bytes, content_type


def extract_tag_value(text: str, tag_name: str) -> str:
    """
    Extract value between XML-style tags.

    Args:
        text: String containing XML-style tags
        tag_name: Name of the tag without angle brackets

    Returns:
        str: Value between the opening and closing tags

    Raises:
        ModelResponseError: If tags cannot be found in text
    """
    start_tag = f"<{tag_name}>"
    end_tag = f"</{tag_name}>"
    start_index = text.find(start_tag) + len(start_tag)
    end_index = text.find(end_tag)
    if start_index == -1 or end_index == -1:
        raise ModelResponseError("Failed to parse output")
    return text[start_index:end_index].strip()
