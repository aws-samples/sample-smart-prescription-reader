# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import pytest
from pydantic import ValidationError

from smart_prescription_reader.models.drug_information import DrugInformation


class TestDrugInformation:
    """Test cases for the DrugInformation model."""

    def test_valid_initialization(self):
        """Test that the model initializes with valid data."""
        drug_info = DrugInformation(
            drug_name="Lisinopril",
            active_ingredient="Lisinopril",
            strength="10 mg",
            form="Tablet"
        )
        
        assert drug_info.drug_name == "Lisinopril"
        assert drug_info.active_ingredient == "Lisinopril"
        assert drug_info.strength == "10 mg"
        assert drug_info.form == "Tablet"

    def test_initialization_with_empty_strings(self):
        """Test that the model initializes with empty strings."""
        drug_info = DrugInformation(
            drug_name="",
            active_ingredient="",
            strength="",
            form=""
        )
        
        assert drug_info.drug_name == ""
        assert drug_info.active_ingredient == ""
        assert drug_info.strength == ""
        assert drug_info.form == ""

    def test_model_dict_representation(self):
        """Test the model's dictionary representation."""
        drug_info = DrugInformation(
            drug_name="Metformin",
            active_ingredient="Metformin Hydrochloride",
            strength="500 mg",
            form="Extended-Release Tablet"
        )
        
        drug_dict = drug_info.model_dump()
        
        assert drug_dict == {
            "drug_name": "Metformin",
            "active_ingredient": "Metformin Hydrochloride",
            "strength": "500 mg",
            "form": "Extended-Release Tablet"
        }

    def test_model_json_serialization(self):
        """Test the model's JSON serialization."""
        drug_info = DrugInformation(
            drug_name="Amoxicillin",
            active_ingredient="Amoxicillin",
            strength="250 mg/5 mL",
            form="Oral Suspension"
        )
        
        json_str = drug_info.model_dump_json()
        
        # Check that the JSON string contains all the expected fields
        assert "Amoxicillin" in json_str
        assert "250 mg/5 mL" in json_str
        assert "Oral Suspension" in json_str