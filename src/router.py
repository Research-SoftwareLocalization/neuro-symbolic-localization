"""
Split Conformal Risk Control & Adaptive Routing Engine
Calculates risk bounds and dynamically routes localization segments 
between lightweight translation memory/NMT and LLM self-correction.
"""

import numpy as np
from typing import List, Dict, Tuple

class ConformalRouter:
    def __init__(self, target_risk_level: float = 0.05):
        """
        Initializes the conformal router.
        :param target_risk_level: Desired upper bound on structural error rate (alpha).
        """
        self.alpha = target_risk_level
        self.risk_threshold: float = 0.0

    def calibrate(self, validation_scores: List[float]) -> float:
        """
        Calibrates the risk threshold using a held-out validation set.
        :param validation_scores: List of uncertainty/error scores on calibration set.
        :return: Computed conformal quantile threshold.
        """
        n = len(validation_scores)
        if n == 0:
            return 0.0
        
        # Calculate the (1 - alpha) quantile with finite-sample correction
        level = np.ceil((n + 1) * (1 - self.alpha)) / n
        level = min(1.0, max(0.0, level))
        
        self.risk_threshold = float(np.quantile(validation_scores, level))
        return self.risk_threshold

    def route(self, segment_uncertainty: float) -> str:
        """
        Determines the processing route for an incoming localization segment.
        Returns: 'cache_or_nmt' if safe, or 'llm_igsc' if correction is required.
        """
        if segment_uncertainty <= self.risk_threshold:
            return "cache_or_nmt"
        else:
            return "llm_igsc"

    def evaluate_routing_efficiency(self, uncertainties: List[float]) -> Dict[str, float]:
        """Evaluates percentage of traffic offloaded to fast paths vs LLM path."""
        if not uncertainties:
            return {"fast_path_ratio": 0.0, "llm_path_ratio": 0.0}
            
        fast_count = sum(1 for u in uncertainties if u <= self.risk_threshold)
        total = len(uncertainties)
        
        fast_ratio = fast_count / total
        return {
            "fast_path_ratio": fast_ratio,
            "llm_path_ratio": 1.0 - fast_ratio
        }
