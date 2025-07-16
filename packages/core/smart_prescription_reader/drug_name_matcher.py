# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

from functools import lru_cache
from typing import Optional

import rapidfuzz


class DrugNameMatcher:
    """A class for finding drug name matches using fuzzy string matching.

    This class implements a memory-safe caching strategy for drug name lookups.
    The caching is implemented through a closure pattern to avoid memory leaks
    that can occur when using lru_cache directly on instance methods.

    Args:
        word_list: List of drug names to match against
        threshold: Minimum similarity score (0-100) for a match. Defaults to 70.
    """

    def __init__(self, word_list: list[str], threshold: int = 70):
        self.word_list = word_list
        self.threshold = threshold
        self._cached_find = self._create_cached_finder()

    def _create_cached_finder(self):
        """Creates a cached function specific to this instance.

        This implementation uses a closure to create an instance-specific cached function.
        This pattern is used because:
        1. We want to cache results based only on the query parameter
        2. Direct use of @lru_cache on methods can cause memory leaks
        3. The word_list and threshold are instance-specific and don't need to be part of the cache key

        Returns:
            A cached function that takes query and limit parameters
        """

        @lru_cache(maxsize=1024)
        def _find(query: str, limit: Optional[int] = None) -> list[tuple[str, int, int | str]]:
            return rapidfuzz.process.extract(
                query.upper(),
                self.word_list,
                scorer=rapidfuzz.fuzz.partial_ratio,
                limit=limit,
                score_cutoff=self.threshold,
            )

        return _find

    def find_matches(self, query: str, limit: Optional[int] = None) -> list[tuple[str, int, int | str]]:
        """Find matching drug names for the given query.

        Args:
            query: The drug name to search for
            limit: Maximum number of matches to return. If None, returns all matches above threshold.

        Returns:
            List of tuples containing (matched_name, score, index)
            Empty list if no matches meet the threshold
        """
        return self._cached_find(query, limit)

    def clear_cache(self) -> None:
        """Clear the LRU cache for this instance.

        This can be useful to free memory if the cache is no longer needed
        or if you want to force fresh matches.
        """
        self._cached_find.cache_clear()

    def list_matches(self, words: list[str]) -> set[str]:
        """
        Process multiple words in batch and return unique matches.

        Args:
            words: List of words to process

        Returns:
            Set of unique matched drug names
        """
        return {match for word in words for match, score, _ in self.find_matches(word.upper())}
