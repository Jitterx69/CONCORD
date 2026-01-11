from typing import List, Dict
from uuid import UUID
from app.models import WorldState, Fact


class ProbabilityEngine:
    """
    Manages the probabilities of different World States.
    Uses Bayesian-like updates when new evidence is found.
    """

    def normalize_probabilities(self, worlds: List[WorldState]) -> None:
        """
        Ensure active world probabilities sum to 1.0
        """
        active_worlds = [w for w in worlds if w.active]
        if not active_worlds:
            return

        total_p = sum(w.probability for w in active_worlds)
        if total_p == 0:
            # Distribute evenly if all zero
            equal_p = 1.0 / len(active_worlds)
            for w in active_worlds:
                w.probability = equal_p
        else:
            for w in active_worlds:
                w.probability = w.probability / total_p

    def update_probabilities(
        self,
        worlds: List[WorldState],
        evidence_fact: Fact,
        supporting_world_ids: List[UUID],
    ) -> None:
        """
        Update probabilities based on new evidence.
        If a fact supports a specific world, its probability increases.
        If it contradicts (is not in) a world, it decreases.
        """
        # Simple Bayesian-inspired heuristic for PoC
        # Evidence boosts supporting worlds by a factor
        BOOST_FACTOR = 1.5
        PENALTY_FACTOR = 0.5

        for w in worlds:
            if not w.active:
                continue

            if w.id in supporting_world_ids:
                w.probability *= BOOST_FACTOR
            else:
                # If this fact is exclusive to other worlds, penalize this one?
                # For PoC, only penalize if it explicitly contradicts.
                # Here we assume if it supports specific worlds, others are less likely.
                w.probability *= PENALTY_FACTOR

        self.normalize_probabilities(worlds)
