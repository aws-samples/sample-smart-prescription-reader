# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.


class RetryableError(Exception):
    pass


class RateLimitError(Exception):
    pass


class ModelResponseError(RetryableError):
    pass


class ModelResponseWarning(UserWarning):
    pass


class MaxTokensExceeded(Exception):
    pass


class InvalidImageContentsError(Exception):
    pass
