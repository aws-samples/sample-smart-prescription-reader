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
