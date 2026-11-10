"""
Neuro-Symbolic Cascade & Invariant-Guided Self-Correction (IGSC) Engine
Coordinates the execution pipeline:
  - Fast-path lookup / NMT gate
  - vLLM generation with structural constraints
  - Closed-loop iterative self-correction using deterministic invariant feedback
"""

from typing import Dict, Tuple, Optional
from src.invariants import audit_segment, verify_placeholder_parity
from src.cache import TranslationMemoryCache
from src.router import ConformalRouter

class IGSCModularCascade:
    def __init__(self, cache: TranslationMemoryCache, router: ConformalRouter, max_retries: int = 3):
        self.cache = cache
        self.router = router
        self.max_retries = max_retries

    def construct_repair_prompt(self, source_text: str, failed_hypothesis: str, audit_results: Dict[str, any]) -> str:
        """
        Translates deterministic verification failures into targeted diagnostic hints 
        for closed-loop LLM self-correction at temperature T=0.0.
        """
        violations = []
        invs = audit_results["invariants"]
        
        if not invs["I_script"]:
            violations.append("- Out-of-alphabet foreign codepoints detected. Ensure strict orthographic script purity.")
        if not invs["I_ph"]:
            err_type = audit_results["ph_error_type"]
            if err_type == "E_omit":
                violations.append("- Missing positional format specifiers (e.g., %s, {0}). All placeholders must be preserved verbatim.")
            elif err_type == "E_halluc":
                violations.append("- Hallucinated extra format specifiers not present in the source string.")
            else:
                violations.append("- Positional placeholder multiset mismatch or index corruption.")
        if not invs["I_acc"]:
            violations.append("- Keyboard mnemonic accelerator ampersand (&) missing or misplaced.")
        if not invs["I_enc"]:
            violations.append("- Subword decoding corruption detected (U+FFFD replacement characters present).")
        if not invs["I_chat"]:
            violations.append("- Conversational AI preamble or framing detected. Output only the raw translated string.")
        if not invs["I_ntt"]:
            violations.append("- Invalid verbatim echo detected for a non-translatable segment.")

        feedback_block = "\n".join(violations)
        
        prompt = (
            f"You are a rigorous software localization error-correction agent.\n"
            f"Source Segment: {source_text}\n"
            f"Previous Translation Attempt: {failed_hypothesis}\n\n"
            f"Validation Failures Identified:\n{feedback_block}\n\n"
            f"Instructions: Correct the translation to eliminate all violations above while preserving exact UI syntax and tone. Output only the corrected translation."
        )
        return prompt

    def process_segment(self, source_text: str, locale: str, baseline_translation_fn) -> Tuple[str, bool, int]:
        """
        Executes the full neuro-symbolic pipeline for a single segment:
          1. Checks TM cache (Tier 1-3).
          2. Runs conformal routing check.
          3. Generates baseline translation, audits via invariants, and executes IGSC loop if needed.
        Returns: (final_translation, success_status, retry_count)
        """
        # Step 1: Check Translation Memory Cache
        cached_tgt, tier = self.cache.get(source_text)
        if cached_tgt:
            audit = audit_segment(source_text, cached_tgt, locale)
            if audit["compliant"]:
                return cached_tgt, True, 0

        # Step 2: Generate initial baseline hypothesis
        hypothesis = baseline_translation_fn(source_text)
        
        # Step 3: Audit initial hypothesis
        audit = audit_segment(source_text, hypothesis, locale)
        if audit["compliant"]:
            self.cache.put(source_text, hypothesis)
            return hypothesis, True, 0

        # Step 4: Closed-Loop Invariant-Guided Self-Correction (IGSC) Loop
        current_hypothesis = hypothesis
        for attempt in range(1, self.max_retries + 1):
            repair_prompt = self.construct_repair_prompt(source_text, current_hypothesis, audit)
            
            # Call generation model with repair prompt at T=0.0
            current_hypothesis = baseline_translation_fn(repair_prompt)
            
            audit = audit_segment(source_text, current_hypothesis, locale)
            if audit["compliant"]:
                self.cache.put(source_text, current_hypothesis)
                return current_hypothesis, True, attempt

        # If max retries exhausted, return best available or fallback
        return current_hypothesis, False, self.max_retries
