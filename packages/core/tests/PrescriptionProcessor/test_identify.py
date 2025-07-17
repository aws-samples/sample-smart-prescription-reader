# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

from unittest.mock import MagicMock

import jinja2
import pytest

from smart_prescription_reader.drug_name_matcher import DrugNameMatcher
from smart_prescription_reader.models.drug_information import DrugInformation
from smart_prescription_reader.models.drug_repository import DrugInformationRepository
from smart_prescription_reader.PrescriptionProcessor.identify import IdentifyMedications


class MockDrugRepository(DrugInformationRepository):
    """Mock implementation of DrugInformationRepository for testing."""

    def __init__(self, drugs=None, drug_names=None):
        self.drugs = drugs or []
        self._drug_names = drug_names or []

    def search_drugs(self, terms, limit_kb=100):
        """Mock implementation that returns drugs containing any of the terms."""
        if not terms:
            return []

        results = []
        for drug in self.drugs:
            for term in terms:
                if term.lower() in drug.drug_name.lower() or term.lower() in drug.active_ingredient.lower():
                    results.append(drug)
                    break
        return results

    def get_drug_name_list(self):
        """Mock implementation that returns all drug names and active ingredients."""
        return self._drug_names


class TestIdentifyMedications:
    """Test cases for the IdentifyMedications class."""

    @pytest.fixture
    def sample_drugs(self):
        """Fixture providing sample drug information."""
        return [
            DrugInformation(drug_name="Lisinopril", active_ingredient="Lisinopril", strength="10 mg", form="Tablet"),
            DrugInformation(
                drug_name="Metformin",
                active_ingredient="Metformin Hydrochloride",
                strength="500 mg",
                form="Extended-Release Tablet",
            ),
            DrugInformation(drug_name="Lipitor", active_ingredient="Atorvastatin", strength="20 mg", form="Tablet"),
        ]

    @pytest.fixture
    def large_sample_drugs(self):
        """Fixture providing a large sample of drug information for testing size limits."""
        # Create a list of 50 drugs with long names and descriptions
        drugs = []
        for i in range(1, 51):
            drug_name = f"Medication{i}" + "X" * 50  # Long drug name
            active_ingredient = f"ActiveIngredient{i}" + "Y" * 50  # Long active ingredient
            strength = f"{i * 10} mg" + "Z" * 20  # Long strength
            form = "Tablet" + "W" * 20  # Long form

            drugs.append(
                DrugInformation(
                    drug_name=drug_name,
                    active_ingredient=active_ingredient,
                    strength=strength,
                    form=form,
                )
            )
        return drugs

    @pytest.fixture
    def sample_drug_names(self):
        """Fixture providing sample drug names."""
        return ["Lisinopril", "Metformin", "Metformin Hydrochloride", "Lipitor", "Atorvastatin"]

    @pytest.fixture
    def mock_bedrock_client(self):
        """Fixture providing a mock Bedrock client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def mock_template_env(self):
        """Fixture providing a mock Jinja2 environment."""
        env = MagicMock(spec=jinja2.Environment)
        template = MagicMock()
        template.render.return_value = "You are a pharmacist looking for drug names."
        env.get_template.return_value = template
        return env

    @pytest.fixture
    def config(self):
        """Fixture providing a sample configuration."""
        return {
            "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
            "temperature": 0.0,
            "max_tokens": 2048,
            "thinking": False,
            "transcribe": False,
            "prompt_cache": False,
            "drug_match_threshold": 80,
        }

    def test_init_with_drug_repository(self, mock_bedrock_client, mock_template_env, config, sample_drugs):
        """Test initialization with drug repository."""
        # Create a mock repository
        repo = MockDrugRepository(drugs=sample_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Check that the repository was set
        assert processor.drug_repository is repo

        # Check that the drug matcher is not initialized yet (lazy loading)
        assert processor._drug_matcher is None

    def test_init_without_drug_repository(self, mock_bedrock_client, mock_template_env, config):
        """Test initialization without drug repository."""
        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config
        )

        # Check that the repository is None
        assert processor.drug_repository is None

        # Check that the drug matcher is None
        assert processor._drug_matcher is None

    def test_drug_matcher_lazy_loading(self, mock_bedrock_client, mock_template_env, config, sample_drug_names):
        """Test lazy loading of drug matcher."""
        # Create a mock repository
        repo = MockDrugRepository(drug_names=sample_drug_names)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Check that the drug matcher is not initialized yet
        assert processor._drug_matcher is None

        # Access the drug_matcher property to trigger lazy loading
        matcher = processor.drug_matcher

        # Check that the drug matcher was initialized
        assert matcher is not None
        assert isinstance(matcher, DrugNameMatcher)
        assert matcher.threshold == 80  # From config

        # Check that the drug matcher is now cached
        assert processor._drug_matcher is matcher

    def test_drug_matcher_with_empty_drug_list(self, mock_bedrock_client, mock_template_env, config):
        """Test drug matcher with empty drug list."""
        # Create a mock repository with empty drug list
        repo = MockDrugRepository(drug_names=[])

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Access the drug_matcher property
        matcher = processor.drug_matcher

        # Check that the drug matcher is None
        assert matcher is None

    def test_drug_matcher_with_repository_error(self, mock_bedrock_client, mock_template_env, config):
        """Test drug matcher when repository raises an error."""
        # Create a mock repository that raises an error
        repo = MagicMock(spec=DrugInformationRepository)
        repo.get_drug_name_list.side_effect = Exception("Test error")

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Access the drug_matcher property
        matcher = processor.drug_matcher

        # Check that the drug matcher is None
        assert matcher is None

        # Check that the repository method was called
        repo.get_drug_name_list.assert_called_once()

    def test_different_configurations(self, mock_bedrock_client, mock_template_env, sample_drug_names):
        """Test initialization with different configurations."""
        # Create a mock repository
        repo = MockDrugRepository(drug_names=sample_drug_names)

        # Test with minimal configuration
        minimal_config = {"model_id": "test-model"}
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client,
            template_env=mock_template_env,
            config=minimal_config,
            drug_repository=repo,
        )

        # Check default values
        assert processor.config["model_id"] == "test-model"
        assert processor.config["temperature"] == 0.0
        assert processor.config["thinking"] is False
        assert processor.config["transcribe"] is False
        assert processor.config["prompt_cache"] is False

        # Access the drug_matcher property to trigger lazy loading
        matcher = processor.drug_matcher

        # Check that the default threshold was used
        assert matcher.threshold == 70  # Default value

        # Test with complete configuration
        complete_config = {
            "model_id": "test-model-2",
            "temperature": 0.5,
            "thinking": True,
            "transcribe": True,
            "prompt_cache": True,
            "drug_match_threshold": 90,
        }

        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client,
            template_env=mock_template_env,
            config=complete_config,
            drug_repository=repo,
        )

        # Check values
        assert processor.config["model_id"] == "test-model-2"
        assert processor.config["temperature"] == 0.5
        assert processor.config["thinking"] is True
        assert processor.config["transcribe"] is True
        assert processor.config["prompt_cache"] is True

        # Access the drug_matcher property to trigger lazy loading
        matcher = processor.drug_matcher

        # Check that the configured threshold was used
        assert matcher.threshold == 90

    def test_find_matching_medications_with_mocked_response(
        self, mock_bedrock_client, mock_template_env, config, sample_drugs
    ):
        """Test find_matching_medications with mocked identify_medications response."""
        # Create a mock repository
        repo = MockDrugRepository(drugs=sample_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the identify_medications method to return specific medications
        processor.identify_medications = MagicMock(return_value=["Lisinopril", "Metformin"])

        # Call the method
        ocr_text = "Patient is taking Lisinopril 10mg and Metformin 500mg daily."
        results = processor.find_matching_medications(ocr_text)

        # Check that identify_medications was called with the OCR text
        processor.identify_medications.assert_called_once_with(ocr_text)

        # Check that the results contain the expected medications
        assert len(results) == 2
        drug_names = {drug.drug_name for drug in results}
        assert "Lisinopril" in drug_names
        assert "Metformin" in drug_names

    def test_find_matching_medications_with_mocked_drug_matcher(
        self, mock_bedrock_client, mock_template_env, config, sample_drugs
    ):
        """Test find_matching_medications with mocked DrugNameMatcher."""
        # Create a mock repository
        repo = MockDrugRepository(drugs=sample_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the identify_medications method
        processor.identify_medications = MagicMock(return_value=["Lisinopril", "Metformin", "Unknown"])

        # Mock the drug_matcher property
        mock_matcher = MagicMock()
        mock_matcher.list_matches.return_value = {"Lisinopril", "Metformin"}
        processor._drug_matcher = mock_matcher

        # Call the method
        ocr_text = "Patient is taking Lisinopril 10mg and Metformin 500mg daily."
        results = processor.find_matching_medications(ocr_text)

        # Check that the drug matcher was used
        mock_matcher.list_matches.assert_called_once_with(["Lisinopril", "Metformin", "Unknown"])

        # Check that the results contain the expected medications
        assert len(results) == 2
        drug_names = {drug.drug_name for drug in results}
        assert "Lisinopril" in drug_names
        assert "Metformin" in drug_names

    def test_find_matching_medications_without_drug_repository(self, mock_bedrock_client, mock_template_env, config):
        """Test find_matching_medications without a drug repository."""
        # Initialize the processor without a drug repository
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config
        )

        # Call the method
        ocr_text = "Patient is taking Lisinopril 10mg and Metformin 500mg daily."
        results = processor.find_matching_medications(ocr_text)

        # Check that the results are empty
        assert len(results) == 0

    def test_find_matching_medications_with_empty_response(
        self, mock_bedrock_client, mock_template_env, config, sample_drugs
    ):
        """Test find_matching_medications with empty identify_medications response."""
        # Create a mock repository
        repo = MockDrugRepository(drugs=sample_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the identify_medications method to return empty list
        processor.identify_medications = MagicMock(return_value=[])

        # Call the method
        ocr_text = "Patient is taking medication daily."
        results = processor.find_matching_medications(ocr_text)

        # Check that the results are empty
        assert len(results) == 0

    def test_find_matching_medications_with_no_matches(
        self, mock_bedrock_client, mock_template_env, config, sample_drugs
    ):
        """Test find_matching_medications when no matches are found."""
        # Create a mock repository
        repo = MockDrugRepository(drugs=sample_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the identify_medications method
        processor.identify_medications = MagicMock(return_value=["Unknown1", "Unknown2"])

        # Mock the drug_matcher property
        mock_matcher = MagicMock()
        mock_matcher.list_matches.return_value = set()  # No matches found
        processor._drug_matcher = mock_matcher

        # Call the method
        ocr_text = "Patient is taking unknown medication daily."
        results = processor.find_matching_medications(ocr_text)

        # Check that the results are empty
        assert len(results) == 0

    def test_find_matching_medications_without_drug_matcher(
        self, mock_bedrock_client, mock_template_env, config, sample_drugs
    ):
        """Test find_matching_medications without a drug matcher."""
        # Create a mock repository
        repo = MockDrugRepository(drugs=sample_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the identify_medications method
        processor.identify_medications = MagicMock(return_value=["Lisinopril", "Metformin"])

        # Set drug_matcher to None to simulate no matcher available
        processor._drug_matcher = None

        # Call the method
        ocr_text = "Patient is taking Lisinopril 10mg and Metformin 500mg daily."
        results = processor.find_matching_medications(ocr_text)

        # Check that the results contain the expected medications
        # In this case, it should use the potential medications directly
        assert len(results) == 2
        drug_names = {drug.drug_name for drug in results}
        assert "Lisinopril" in drug_names
        assert "Metformin" in drug_names

    def test_find_matching_medications_error_handling(
        self, mock_bedrock_client, mock_template_env, config, sample_drugs
    ):
        """Test error handling in find_matching_medications."""
        # Create a mock repository
        repo = MockDrugRepository(drugs=sample_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the identify_medications method to raise an exception
        processor.identify_medications = MagicMock(side_effect=Exception("Test error"))

        # Call the method
        ocr_text = "Patient is taking Lisinopril 10mg and Metformin 500mg daily."
        results = processor.find_matching_medications(ocr_text)

        # Check that the results are empty due to error handling
        assert len(results) == 0

    def test_get_medication_context_with_medications(
        self, mock_bedrock_client, mock_template_env, config, sample_drugs
    ):
        """Test get_medication_context with medications."""
        # Create a mock repository
        repo = MockDrugRepository(drugs=sample_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the find_matching_medications method to return specific medications
        processor.find_matching_medications = MagicMock(return_value=sample_drugs)

        # Call the method
        ocr_text = "Patient is taking Lisinopril 10mg and Metformin 500mg daily."
        context = processor.get_medication_context(ocr_text)

        # Check that find_matching_medications was called with the OCR text
        processor.find_matching_medications.assert_called_once_with(ocr_text, limit_kb=100)

        # Check that the context contains the expected information
        assert "##Medication Information##" in context
        assert "Use this information to help correct transcription errors:" in context
        assert "- Lisinopril: 10 mg Tablet" in context
        assert "- Metformin (Metformin Hydrochloride): 500 mg Extended-Release Tablet" in context
        assert "- Lipitor (Atorvastatin): 20 mg Tablet" in context

    def test_get_medication_context_empty_results(self, mock_bedrock_client, mock_template_env, config):
        """Test get_medication_context with empty results."""
        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config
        )

        # Mock the find_matching_medications method to return empty list
        processor.find_matching_medications = MagicMock(return_value=[])

        # Call the method
        ocr_text = "Patient is taking medication daily."
        context = processor.get_medication_context(ocr_text)

        # Check that find_matching_medications was called with the OCR text
        processor.find_matching_medications.assert_called_once_with(ocr_text, limit_kb=100)

        # Check that the context is empty
        assert context == ""

    def test_get_medication_context_repository_size_limiting(
        self, mock_bedrock_client, mock_template_env, config, large_sample_drugs
    ):
        """Test that get_medication_context passes size limits to the repository."""
        # Create a mock repository with size limiting behavior
        repo = MockDrugRepository()

        # Override the search_drugs method to simulate size limiting
        limited_drugs = large_sample_drugs[:10]  # Only return first 10 drugs
        repo.search_drugs = MagicMock(return_value=limited_drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the identify_medications method to return medication names
        processor.identify_medications = MagicMock(return_value=["Med1", "Med2"])

        # Call the method with a custom size limit
        ocr_text = "Patient is taking multiple medications."
        context = processor.get_medication_context(ocr_text, limit_kb=10)

        # Check that the repository's search_drugs was called with the limit_kb parameter
        repo.search_drugs.assert_called_once()
        args, kwargs = repo.search_drugs.call_args
        assert kwargs.get("limit_kb") == 10

        # Check that the context is not empty
        assert context != ""

        # Check that the context contains only the medications returned by the repository
        assert len(context.split("\n")) == len(limited_drugs) + 2  # +2 for header lines

        # Check that the context contains the expected header information
        assert "##Medication Information##" in context
        assert "Use this information to help correct transcription errors:" in context

    def test_get_medication_context_formatting(self, mock_bedrock_client, mock_template_env, config):
        """Test formatting of medication context with different drug information."""
        # Create drugs with different combinations of fields
        drugs = [
            # Complete information
            DrugInformation(drug_name="Drug1", active_ingredient="Active1", strength="10 mg", form="Tablet"),
            # Missing form
            DrugInformation(drug_name="Drug2", active_ingredient="Active2", strength="20 mg", form=""),
            # Missing strength
            DrugInformation(drug_name="Drug3", active_ingredient="Active3", strength="", form="Capsule"),
            # Missing strength and form
            DrugInformation(drug_name="Drug4", active_ingredient="Active4", strength="", form=""),
            # Same drug name and active ingredient
            DrugInformation(drug_name="Drug5", active_ingredient="Drug5", strength="30 mg", form="Tablet"),
        ]

        # Create a mock repository
        repo = MockDrugRepository(drugs=drugs)

        # Initialize the processor
        processor = IdentifyMedications(
            bedrock_client=mock_bedrock_client, template_env=mock_template_env, config=config, drug_repository=repo
        )

        # Mock the find_matching_medications method
        processor.find_matching_medications = MagicMock(return_value=drugs)

        # Call the method
        ocr_text = "Patient is taking multiple medications."
        context = processor.get_medication_context(ocr_text)

        # Check formatting for each case
        assert "- Drug1 (Active1): 10 mg Tablet" in context
        assert "- Drug2 (Active2): 20 mg" in context
        assert "- Drug3 (Active3): Capsule" in context
        assert "- Drug4 (Active4)" in context
        assert "- Drug5: 30 mg Tablet" in context  # No active ingredient in parentheses
