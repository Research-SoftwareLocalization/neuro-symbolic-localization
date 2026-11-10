"""
Three-Tier Contextual Translation Memory Cache for Software Localization
Provides high-performance caching and retrieval across three tiers:
  - Tier 1: Verbatim Exact Match (O(1) lookup on raw source string)
  - Tier 2: Normalized Match (Whitespace and case-insensitive normalization)
  - Tier 3: Fuzzy Similarity Match (Levenshtein/difflib threshold matching for UI fragments)
"""

import json
import os
from difflib import SequenceMatcher
from typing import Optional, Dict

class TranslationMemoryCache:
    def __init__(self, cache_filepath: Optional[str] = None, fuzzy_threshold: float = 0.92):
        self.cache_filepath = cache_filepath
        self.fuzzy_threshold = fuzzy_threshold
        self.verbatim_store: Dict[str, str] = {}
        self.normalized_store: Dict[str, str] = {}
        
        if cache_filepath and os.path.exists(cache_filepath):
            self.load_cache(cache_filepath)

    def _normalize_key(self, text: str) -> str:
        """Normalizes source strings for Tier 2 matching (strips whitespace, lowercases)."""
        return " ".join(text.strip().lower().split())

    def get(self, source_text: str) -> Tuple[Optional[str], str]:
        """
        Queries the 3-tier translation memory.
        Returns: (translated_text, tier_matched)
        """
        # Tier 1: Verbatim Exact Match
        if source_text in self.verbatim_store:
            return self.verbatim_store[source_text], "Tier1_Verbatim"

        # Tier 2: Normalized Match
        norm_key = self._normalize_key(source_text)
        if norm_key in self.normalized_store:
            return self.normalized_store[norm_key], "Tier2_Normalized"

        # Tier 3: Fuzzy Match across verbatim keys
        best_match = None
        highest_ratio = 0.0
        for cached_src, translation in self.verbatim_store.items():
            ratio = SequenceMatcher(None, source_text, cached_src).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = translation

        if highest_ratio >= self.fuzzy_threshold and best_match:
            return best_match, "Tier3_Fuzzy"

        return None, "Miss"

    def put(self, source_text: str, target_text: str) -> None:
        """Stores a validated translation into Tier 1 and Tier 2 indices."""
        self.verbatim_store[source_text] = target_text
        norm_key = self._normalize_key(source_text)
        self.normalized_store[norm_key] = target_text

    def save_cache(self, filepath: Optional[str] = None) -> None:
        """Persists the translation memory store to disk as JSON."""
        target_path = filepath or self.cache_filepath
        if target_path:
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self.verbatim_store, f, ensure_ascii=False, indent=2)

    def load_cache(self, filepath: str) -> None:
        """Loads a pre-existing translation memory store from JSON."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for src, tgt in data.items():
                    self.put(src, tgt)
