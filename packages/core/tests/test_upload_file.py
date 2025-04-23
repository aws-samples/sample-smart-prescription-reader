# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

from unittest.mock import MagicMock, patch

from smart_prescription_reader.upload_file import upload_file


@patch("smart_prescription_reader.upload_file.create_presigned_url")
def test_upload_file(mock_create_presigned_url, monkeypatch):
    url = "https://test-bucket.s3.amazonaws.com/test-file.png?TESTSTRING"
    mock_create_presigned_url.return_value = url

    s3_client = MagicMock()
    response = upload_file(
        s3_client=s3_client,
        file_name="test_file.png",
        input_bucket="test-bucket",
    )

    mock_create_presigned_url.assert_called_once()

    assert response.url == url
