# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

"""Unit tests configuration module."""

import pytest
from dotenv import find_dotenv, load_dotenv

pytest_plugins = []


@pytest.fixture(scope="class")
def integration_env():
    load_dotenv(find_dotenv(".env.integration"))
