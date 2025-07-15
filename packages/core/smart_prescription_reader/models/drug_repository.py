# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

import logging
import os
import sqlite3
import tempfile
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Optional, Dict, Any

import boto3
import botocore.exceptions

from smart_prescription_reader.models.drug_information import DrugInformation
from smart_prescription_reader.utils import get_s3_client

logger = logging.getLogger(__name__)


class DrugInformationRepository(ABC):
    """Abstract base class for drug information repositories.
    
    This interface defines the contract for accessing medication information.
    Implementations can use different storage mechanisms (SQLite, DynamoDB, etc.)
    while providing a consistent interface for medication lookup.
    """
    
    @abstractmethod
    def search_drugs(self, terms: List[str], limit_kb: int = 100) -> List[DrugInformation]:
        """Search for drugs by terms across both drug names and active ingredients.
        
        Args:
            terms: List of search terms
            limit_kb: Maximum size of results in KB
            
        Returns:
            List of DrugInformation objects matching the search terms
        """
        pass
    
    @abstractmethod
    def get_drug_name_list(self) -> List[str]:
        """Get a list of all drug names and active ingredients for fuzzy matching.
        
        Returns:
            List of drug names and active ingredients for fuzzy matching
        """
        pass


class SQLiteDrugRepository(DrugInformationRepository):
    """SQLite implementation of DrugInformationRepository.
    
    This implementation uses a SQLite database stored in S3 for efficient access
    to medication details. The database is downloaded and cached locally on
    initialization.
    
    Attributes:
        s3_bucket: S3 bucket containing the database
        s3_key: S3 key for the database file
        db_path: Path to the local database file
        local_cache_dir: Directory to cache downloaded files
        word_list_s3_key: S3 key for pre-built word list
    """
    
    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None,
        local_db_path: Optional[str] = None,
        local_cache_dir: Optional[str] = None,
        word_list_s3_key: Optional[str] = None
    ):
        """Initialize with S3 location and optional cache directory.
        
        Args:
            s3_bucket: S3 bucket containing the database (optional if local_db_path provided)
            s3_key: S3 key for the database file (optional if local_db_path provided)
            local_db_path: Direct path to a local database file (bypasses S3 download)
            local_cache_dir: Directory to cache downloaded files (default: tempdir)
            word_list_s3_key: S3 key for pre-built word list (optional)
        """
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.local_cache_dir = local_cache_dir or tempfile.gettempdir()
        self.word_list_s3_key = word_list_s3_key
        
        # If local_db_path is provided, use it directly
        if local_db_path:
            self.db_path = local_db_path
        else:
            # Otherwise, construct a path in the cache directory
            if not s3_bucket or not s3_key:
                raise ValueError("Either local_db_path or both s3_bucket and s3_key must be provided")
            
            # Create a filename based on the S3 key
            filename = os.path.basename(s3_key)
            self.db_path = os.path.join(self.local_cache_dir, filename)
        
        # Cache for drug name list
        self._drug_name_list = None
        
        # Ensure database is available
        self._ensure_database()
    
    def _ensure_database(self) -> None:
        """Download database from S3 if not already cached.
        
        This method checks if the database file exists locally. If not, it
        downloads the file from S3 and stores it in the cache directory.
        
        Raises:
            ValueError: If S3 bucket or key is not provided and local file doesn't exist
            botocore.exceptions.ClientError: If there's an error accessing S3
        """
        # If the database file already exists, we're done
        if os.path.exists(self.db_path):
            logger.debug(f"Using cached database at {self.db_path}")
            return
        
        # If we don't have S3 info, we can't download
        if not self.s3_bucket or not self.s3_key:
            raise ValueError(f"Database file {self.db_path} not found and no S3 location provided")
        
        # Create cache directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Download the database file from S3
        logger.info(f"Downloading database from s3://{self.s3_bucket}/{self.s3_key} to {self.db_path}")
        try:
            s3_client = get_s3_client()
            s3_client.download_file(self.s3_bucket, self.s3_key, self.db_path)
            logger.info(f"Successfully downloaded database to {self.db_path}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error downloading database: {e}")
            # Remove the file if it was partially downloaded
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            raise
    
    def search_drugs(self, terms: List[str], limit_kb: int = 100) -> List[DrugInformation]:
        """Search for drugs by terms across both drug names and active ingredients.
        
        This method searches for drugs where either the drug name or active ingredient
        contains any of the provided terms. The search is case-insensitive.
        
        Args:
            terms: List of search terms
            limit_kb: Maximum size of results in KB
            
        Returns:
            List of DrugInformation objects matching the search terms
            
        Raises:
            sqlite3.Error: If there's an error executing the query
        """
        if not terms:
            return []
        
        try:
            # Ensure database is available
            self._ensure_database()
            
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create the WHERE clause dynamically with OR conditions
            where_conditions = []
            params = []
            for term in terms:
                where_conditions.append(
                    "(drug_name LIKE ? OR active_ingredient LIKE ?)"
                )
                params.extend([f"%{term}%", f"%{term}%"])
            
            query = f"""
                SELECT drug_name, active_ingredient, strength, form
                FROM drugs
                WHERE {" OR ".join(where_conditions)}
            """
            
            # Execute the query
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Convert to DrugInformation objects
            drug_info_list = [
                DrugInformation(
                    drug_name=row[0],
                    active_ingredient=row[1],
                    strength=row[2],
                    form=row[3]
                )
                for row in results
            ]
            
            # Filter results to fit within size limit
            filtered_results = self._filter_results_to_size(drug_info_list, limit_kb)
            
            # Close the connection
            conn.close()
            
            return filtered_results
            
        except sqlite3.Error as e:
            logger.error(f"Error searching drugs: {e}")
            # Return empty list on error
            return []
    
    def get_drug_name_list(self) -> List[str]:
        """Get a list of all drug names and active ingredients for fuzzy matching.
        
        This method will:
        1. Try to load a pre-built word list from S3 if word_list_s3_key was provided
        2. Generate the list from the database if no pre-built list exists
        3. Cache the generated list in memory for subsequent calls
        
        Returns:
            List of drug names and active ingredients for fuzzy matching
            
        Raises:
            sqlite3.Error: If there's an error executing the query
        """
        # Return cached list if available
        if self._drug_name_list is not None:
            return self._drug_name_list
        
        # Try to load pre-built word list from S3
        if self.s3_bucket and self.word_list_s3_key:
            try:
                s3_client = get_s3_client()
                response = s3_client.get_object(Bucket=self.s3_bucket, Key=self.word_list_s3_key)
                content = response['Body'].read().decode('utf-8')
                self._drug_name_list = [line.strip() for line in content.splitlines() if line.strip()]
                logger.info(f"Loaded {len(self._drug_name_list)} drug names from S3")
                return self._drug_name_list
            except botocore.exceptions.ClientError as e:
                logger.warning(f"Could not load word list from S3: {e}")
                # Fall back to generating from database
        
        # Generate from database
        self._drug_name_list = self._generate_drug_name_list()
        return self._drug_name_list
    
    def _generate_drug_name_list(self) -> List[str]:
        """Generate a list of drug names and active ingredients from the database.
        
        Returns:
            List of unique drug names and active ingredients
            
        Raises:
            sqlite3.Error: If there's an error executing the query
        """
        try:
            # Ensure database is available
            self._ensure_database()
            
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all drug names
            cursor.execute("SELECT drug_name FROM drugs")
            drug_names = [row[0] for row in cursor.fetchall()]
            
            # Get all active ingredients
            cursor.execute("SELECT active_ingredient FROM drugs")
            active_ingredients = [row[0] for row in cursor.fetchall()]
            
            # Close the connection
            conn.close()
            
            # Combine and deduplicate
            all_names = set(drug_names + active_ingredients)
            
            # Remove empty strings
            all_names = [name for name in all_names if name.strip()]
            
            logger.info(f"Generated {len(all_names)} drug names from database")
            return sorted(all_names)
            
        except sqlite3.Error as e:
            logger.error(f"Error generating drug name list: {e}")
            # Return empty list on error
            return []
    
    def _estimate_size_kb(self, results: List[DrugInformation]) -> float:
        """Estimate the size of results in KB.
        
        Args:
            results: List of DrugInformation objects
            
        Returns:
            Estimated size in KB
        """
        # Estimate size based on string lengths
        total_bytes = 0
        for drug in results:
            # Add approximate overhead for object structure
            total_bytes += 100
            
            # Add string lengths
            total_bytes += len(drug.drug_name.encode('utf-8'))
            total_bytes += len(drug.active_ingredient.encode('utf-8'))
            total_bytes += len(drug.strength.encode('utf-8'))
            total_bytes += len(drug.form.encode('utf-8'))
        
        # Convert to KB
        return total_bytes / 1024
    
    def _filter_results_to_size(self, results: List[DrugInformation], limit_kb: int) -> List[DrugInformation]:
        """Filter results to fit within size limit.
        
        This method implements adaptive filtering to limit result size while
        preserving the most relevant results.
        
        Args:
            results: List of DrugInformation objects
            limit_kb: Maximum size in KB
            
        Returns:
            Filtered list of DrugInformation objects
        """
        # If results are already within limit, return as is
        estimated_size = self._estimate_size_kb(results)
        if estimated_size <= limit_kb:
            logger.debug(f"Results size ({estimated_size:.2f} KB) within limit ({limit_kb} KB)")
            return results
        
        # Calculate how many results we can include
        avg_size_per_result = estimated_size / len(results) if results else 0
        max_results = int(limit_kb / avg_size_per_result) if avg_size_per_result > 0 else 0
        
        # Ensure we have at least one result
        max_results = max(1, max_results)
        
        # Truncate results
        filtered = results[:max_results]
        
        logger.info(
            f"Limited results from {len(results)} to {len(filtered)} to fit within {limit_kb} KB "
            f"(estimated size: {self._estimate_size_kb(filtered):.2f} KB)"
        )
        
        return filtered