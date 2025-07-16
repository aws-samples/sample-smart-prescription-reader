# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import os
import sqlite3
import tempfile
from unittest.mock import MagicMock, patch

import botocore.exceptions
import pytest

from smart_prescription_reader.models.drug_information import DrugInformation
from smart_prescription_reader.models.drug_repository import DrugInformationRepository, SQLiteDrugRepository


class MockDrugRepository(DrugInformationRepository):
    """Mock implementation of DrugInformationRepository for testing."""

    def __init__(self, drugs: list[DrugInformation] = None):
        self.drugs = drugs or []

    def search_drugs(self, terms: list[str], limit_kb: int = 100) -> list[DrugInformation]:
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

    def get_drug_name_list(self) -> list[str]:
        """Mock implementation that returns all drug names and active ingredients."""
        names = []
        for drug in self.drugs:
            names.append(drug.drug_name)
            if drug.active_ingredient != drug.drug_name:
                names.append(drug.active_ingredient)
        return names


class TestDrugInformationRepository:
    """Test cases for the DrugInformationRepository interface."""

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

    def test_search_drugs_implementation(self, sample_drugs):
        """Test that the search_drugs method works as expected."""
        repo = MockDrugRepository(sample_drugs)

        # Search by drug name
        results = repo.search_drugs(["Lisinopril"])
        assert len(results) == 1
        assert results[0].drug_name == "Lisinopril"

        # Search by active ingredient
        results = repo.search_drugs(["Atorvastatin"])
        assert len(results) == 1
        assert results[0].drug_name == "Lipitor"

        # Search with multiple terms
        results = repo.search_drugs(["Metformin", "Lisinopril"])
        assert len(results) == 2
        assert {drug.drug_name for drug in results} == {"Metformin", "Lisinopril"}

        # Search with non-matching term
        results = repo.search_drugs(["Aspirin"])
        assert len(results) == 0

        # Search with empty terms list
        results = repo.search_drugs([])
        assert len(results) == 0

    def test_get_drug_name_list_implementation(self, sample_drugs):
        """Test that the get_drug_name_list method works as expected."""
        repo = MockDrugRepository(sample_drugs)

        drug_names = repo.get_drug_name_list()

        # Check that all drug names are included
        assert "Lisinopril" in drug_names
        assert "Metformin" in drug_names
        assert "Lipitor" in drug_names

        # Check that distinct active ingredients are included
        assert "Metformin Hydrochloride" in drug_names
        assert "Atorvastatin" in drug_names

        # Check that duplicate names are not included twice
        # (Lisinopril is both drug name and active ingredient)
        assert drug_names.count("Lisinopril") == 1


class TestSQLiteDrugRepository:
    """Test cases for the SQLiteDrugRepository implementation."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary SQLite database with test data."""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # Connect to the database
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # Create table
        cursor.execute("""
            CREATE TABLE drugs (
                drug_name TEXT,
                active_ingredient TEXT,
                strength TEXT,
                form TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_drug_name ON drugs(drug_name COLLATE NOCASE)")
        cursor.execute("CREATE INDEX idx_active_ingredient ON drugs(active_ingredient COLLATE NOCASE)")

        # Insert test data
        test_data = [
            ("Lisinopril", "Lisinopril", "10 mg", "Tablet"),
            ("Metformin", "Metformin Hydrochloride", "500 mg", "Extended-Release Tablet"),
            ("Lipitor", "Atorvastatin", "20 mg", "Tablet"),
            ("Amoxicillin", "Amoxicillin", "250 mg/5 mL", "Oral Suspension"),
            ("Prozac", "Fluoxetine", "20 mg", "Capsule"),
            ("Ventolin", "Albuterol", "90 mcg", "Inhaler"),
            ("Fexofenadine", "Fexofenadine Hydrochloride", "180 mg", "Tablet"),
            ("Flonase", "Fluticasone", "50 mcg", "Nasal Spray"),
        ]

        cursor.executemany(
            "INSERT INTO drugs (drug_name, active_ingredient, strength, form) VALUES (?, ?, ?, ?)", test_data
        )

        # Commit and close
        conn.commit()
        conn.close()

        yield path

        # Clean up
        os.unlink(path)

    @pytest.fixture
    def temp_word_list_path(self):
        """Create a temporary word list file."""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)

        # Write test data
        with open(path, "w") as f:
            f.write("LISINOPRIL\n")
            f.write("METFORMIN\n")
            f.write("METFORMIN HYDROCHLORIDE\n")
            f.write("LIPITOR\n")
            f.write("ATORVASTATIN\n")

        yield path

        # Clean up
        os.unlink(path)

    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client for testing."""
        with patch("smart_prescription_reader.models.drug_repository.get_s3_client") as mock:
            s3_client = MagicMock()
            mock.return_value = s3_client
            yield s3_client

    def test_init_with_local_path(self, temp_db_path):
        """Test initialization with local database path."""
        repo = SQLiteDrugRepository(local_db_path=temp_db_path)

        assert repo.db_path == temp_db_path
        assert repo.s3_bucket is None
        assert repo.s3_key is None

    def test_init_with_s3_path_existing_file(self, temp_db_path, mock_s3_client):
        """Test initialization with S3 path when file already exists locally."""
        # Create a temporary directory for caching
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the database to the cache directory
            cache_path = os.path.join(temp_dir, "drugs.db")
            with open(temp_db_path, "rb") as src, open(cache_path, "wb") as dst:
                dst.write(src.read())

            # Initialize repository
            repo = SQLiteDrugRepository(s3_bucket="test-bucket", s3_key="data/drugs.db", local_cache_dir=temp_dir)

            assert repo.db_path == cache_path
            assert repo.s3_bucket == "test-bucket"
            assert repo.s3_key == "data/drugs.db"

            # S3 client should not be called
            mock_s3_client.download_file.assert_not_called()

    def test_init_with_s3_path_download(self, mock_s3_client):
        """Test initialization with S3 path when file needs to be downloaded."""
        # Create a temporary directory for caching
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize repository
            repo = SQLiteDrugRepository(s3_bucket="test-bucket", s3_key="data/drugs.db", local_cache_dir=temp_dir)

            expected_path = os.path.join(temp_dir, "drugs.db")
            assert repo.db_path == expected_path

            # S3 client should be called to download the file
            mock_s3_client.download_file.assert_called_once_with("test-bucket", "data/drugs.db", expected_path)

    def test_init_with_invalid_params(self):
        """Test initialization with invalid parameters."""
        # Neither local path nor S3 info
        with pytest.raises(ValueError):
            SQLiteDrugRepository()

        # S3 bucket but no key
        with pytest.raises(ValueError):
            SQLiteDrugRepository(s3_bucket="test-bucket")

        # S3 key but no bucket
        with pytest.raises(ValueError):
            SQLiteDrugRepository(s3_key="data/drugs.db")

    def test_search_drugs(self, temp_db_path):
        """Test searching for drugs."""
        repo = SQLiteDrugRepository(local_db_path=temp_db_path)

        # Search by drug name
        results = repo.search_drugs(["Lisinopril"])
        assert len(results) == 1
        assert results[0].drug_name == "Lisinopril"

        # Search by active ingredient
        results = repo.search_drugs(["Atorvastatin"])
        assert len(results) == 1
        assert results[0].drug_name == "Lipitor"

        # Search with multiple terms
        results = repo.search_drugs(["Metformin", "Lisinopril"])
        assert len(results) == 2
        assert {drug.drug_name for drug in results} == {"Metformin", "Lisinopril"}

        # Search with partial match (using SQL LIKE which requires % for wildcards)
        results = repo.search_drugs(["Met"])
        assert len(results) == 1
        assert results[0].drug_name == "Metformin"

        # Search with non-matching term
        results = repo.search_drugs(["Aspirin"])
        assert len(results) == 0

        # Search with empty terms list
        results = repo.search_drugs([])
        assert len(results) == 0

    def test_search_drugs_case_insensitive(self, temp_db_path):
        """Test that search is case-insensitive."""
        repo = SQLiteDrugRepository(local_db_path=temp_db_path)

        # Search with lowercase
        results_lower = repo.search_drugs(["lisinopril"])

        # Search with uppercase
        results_upper = repo.search_drugs(["LISINOPRIL"])

        # Search with mixed case
        results_mixed = repo.search_drugs(["LiSiNoPrIl"])

        # All should return the same result
        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1
        assert results_lower[0].drug_name == results_upper[0].drug_name == results_mixed[0].drug_name

    def test_get_drug_name_list_from_db(self, temp_db_path):
        """Test getting drug name list from database."""
        repo = SQLiteDrugRepository(local_db_path=temp_db_path)

        drug_names = repo.get_drug_name_list()

        # Check that all drug names are included
        assert "Lisinopril" in drug_names
        assert "Metformin" in drug_names
        assert "Lipitor" in drug_names

        # Check that distinct active ingredients are included
        assert "Metformin Hydrochloride" in drug_names
        assert "Atorvastatin" in drug_names

        # Check total count (8 drugs with some shared active ingredients)
        assert len(drug_names) > 8

    def test_get_drug_name_list_from_s3(self, temp_word_list_path, mock_s3_client):
        """Test getting drug name list from S3."""
        # Mock S3 response
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: b"LISINOPRIL\nMETFORMIN\nATORVASTATIN\nLIPITOR\n")
        }

        # Initialize repository with word list S3 key
        repo = SQLiteDrugRepository(
            s3_bucket="test-bucket",
            s3_key="data/drugs.db",
            word_list_s3_key="data/drug-list.txt",
            local_db_path=temp_word_list_path,  # Use this as a placeholder
        )

        drug_names = repo.get_drug_name_list()

        # Check that names from S3 are included
        assert "LISINOPRIL" in drug_names
        assert "METFORMIN" in drug_names
        assert "ATORVASTATIN" in drug_names
        assert "LIPITOR" in drug_names

        # S3 client should be called to get the word list
        mock_s3_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="data/drug-list.txt")

    def test_get_drug_name_list_s3_fallback(self, temp_db_path, mock_s3_client):
        """Test fallback to database when S3 word list fails."""
        # Mock S3 error
        mock_s3_client.get_object.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
        )

        # Initialize repository with word list S3 key
        repo = SQLiteDrugRepository(
            s3_bucket="test-bucket",
            s3_key="data/drugs.db",
            word_list_s3_key="data/drug-list.txt",
            local_db_path=temp_db_path,
        )

        drug_names = repo.get_drug_name_list()

        # Check that names from database are included
        assert "Lisinopril" in drug_names
        assert "Metformin" in drug_names
        assert "Lipitor" in drug_names

        # S3 client should be called to get the word list
        mock_s3_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="data/drug-list.txt")

    def test_size_limiting(self, temp_db_path):
        """Test that results are limited by size."""
        repo = SQLiteDrugRepository(local_db_path=temp_db_path)

        # Set a very small size limit
        small_limit = 0.1  # 0.1 KB

        # Search for all drugs
        results = repo.search_drugs(["i"], limit_kb=small_limit)

        # Should return at least one result but fewer than all matching drugs
        assert len(results) >= 1
        assert len(results) < 8  # We have 8 test drugs, most contain 'i'

    def test_estimate_size(self, temp_db_path):
        """Test size estimation."""
        repo = SQLiteDrugRepository(local_db_path=temp_db_path)

        # Create a sample drug with known size
        drug = DrugInformation(
            drug_name="X" * 1000,  # 1000 bytes
            active_ingredient="Y" * 1000,  # 1000 bytes
            strength="Z" * 1000,  # 1000 bytes
            form="W" * 1000,  # 1000 bytes
        )

        # Estimate size
        size_kb = repo._estimate_size_kb([drug])

        # Should be approximately 4000 bytes + overhead, converted to KB
        assert size_kb > 4.0  # At least 4 KB
        assert size_kb < 5.0  # But not too much more with overhead
