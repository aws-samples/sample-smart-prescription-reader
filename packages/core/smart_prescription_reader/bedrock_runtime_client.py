# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.
import logging
from collections.abc import Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    NotRequired,
    TypedDict,
    Union,
    Unpack,
)

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from smart_prescription_reader.exceptions import (
    ModelResponseError,
    RateLimitError,
    RetryableError,
)

if TYPE_CHECKING:
    # mypy_boto3_* is a test-dependency only and not available at runtime
    # It is also only ever used as type-hints, so we can import it during TYPE_CHECKING only
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
    from mypy_boto3_bedrock_runtime.type_defs import (
        ConverseResponseTypeDef,
        GuardrailConfigurationTypeDef,
        InferenceConfigurationTypeDef,
        MessageOutputTypeDef,
        MessageTypeDef,
        PerformanceConfigurationTypeDef,
        PromptVariableValuesTypeDef,
        SystemContentBlockTypeDef,
        ToolConfigurationTypeDef,
    )

logger = logging.getLogger(__name__)


class InvokeModelInput(TypedDict):
    modelId: str
    messages: Sequence[Union["MessageTypeDef", "MessageOutputTypeDef"]]
    system: NotRequired[Sequence["SystemContentBlockTypeDef"]]
    inferenceConfig: NotRequired["InferenceConfigurationTypeDef"]
    toolConfig: NotRequired["ToolConfigurationTypeDef"]
    guardrailConfig: NotRequired["GuardrailConfigurationTypeDef"]
    additionalModelRequestFields: NotRequired[Mapping[str, Any]]
    promptVariables: NotRequired[Mapping[str, "PromptVariableValuesTypeDef"]]
    additionalModelResponseFieldPaths: NotRequired[Sequence[str]]
    requestMetadata: NotRequired[Mapping[str, str]]
    performanceConfig: NotRequired["PerformanceConfigurationTypeDef"]


def handle_bedrock_errors(func):
    """
    Decorator to convert boto3 Bedrock errors into our exceptions.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if hasattr(e, "response"):
                if e.response["Error"]["Code"] == "ThrottlingException":
                    print(e.response["Error"]["Code"])
                    raise RateLimitError(e) from e
                elif e.response["Error"]["Code"] in (
                        "ModelTimeoutException",
                        "InternalServerException",
                        "ServiceUnavailableException",
                ):
                    print(e)
                    raise RetryableError(e) from e
                else:
                    raise e
            else:
                raise e

    return wrapper


def retry_bedrock_errors(func):
    """
    Decorator to retry function calls up to 10 times on RateLimitError and 3 times on RetryableError.
    """

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(10),
        wait=wait_random_exponential(multiplier=2, max=60, min=30),
        reraise=True,
    )
    @retry(
        retry=retry_if_exception_type(RetryableError),
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(multiplier=2, max=60),
        reraise=True,
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@handle_bedrock_errors
def invoke_model_with_input(
        bedrock_runtime: "BedrockRuntimeClient", **input: Unpack[InvokeModelInput]
) -> "ConverseResponseTypeDef":
    """
    Invoke a model with the given input

    Args:
        bedrock_runtime: The Bedrock runtime client.
        input: The input schema for the model.

    Returns:
        The output of the model.

    Raises:
        ModelResponseError: If the model does not return a structured output with tool use.
    """
    logger.debug(input.get("system"))
    response = bedrock_runtime.converse(**input)
    logger.info(
        {
            "modelUsage": {
                "model": input["modelId"],
                "usage": response["usage"],
            }
        }
    )
    return response


@retry_bedrock_errors
def invoke_model_with_input_retry(
        bedrock_runtime: "BedrockRuntimeClient", **input: Unpack[InvokeModelInput]
) -> "ConverseResponseTypeDef":
    """
    Invoke a model with the given input

    Args:
        bedrock_runtime: The Bedrock runtime client.
        input: The input schema for the model.

    Returns:
        The output of the model.

    Raises:
        ModelResponseError: If the model does not return a structured output with tool use.
    """
    return invoke_model_with_input(bedrock_runtime, **input)


def extract_response_text(response: dict) -> str:
    try:
        content_blocks = response["output"]["message"]["content"]
        text_parts = []

        for block in content_blocks:
            # Only include blocks that have a direct 'text' field
            if "text" in block:
                text_parts.append(block["text"])

        if not text_parts:
            raise KeyError("No text content found in response")

        return "\n".join(text_parts)

    except KeyError as e:
        logger.debug(f"Failed to get prediction from response: {response}")
        raise ModelResponseError("Failed to get prediction from response") from e


def build_full_response(response: dict, response_open: str = "", response_close: str = "") -> str:
    text = extract_response_text(response)
    if response["stopReason"] == "stop_sequence":
        return response_open + text + response_close
    elif response["stopReason"] == "end_turn" and text.endswith(response_close):
        return response_open + text
    else:
        logger.debug(
            {
                "stopReason": response["stopReason"],
                "text": text,
                "response_open": response_open,
                "response_close": response_close,
            }
        )
        raise ModelResponseError(response["stopReason"])
