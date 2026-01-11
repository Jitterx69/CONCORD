"""
Entity Tracker - Core CONCORD Component

Monitors entity behavior and attribute consistency throughout the narrative.
Tracks character traits, object properties, location patterns, and relationship dynamics.
"""

from typing import List, Dict, Any, Optional, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from datetime import datetime

from app.models import (
    Entity,
    EntityType,
    ConsistencyIssue,
    ConsistencyLevel,
    ConstraintType,
)


@dataclass
class EntityState:
    """Tracks the state of an entity at a point in the narrative."""

    entity_id: UUID
    position: int
    attributes: Dict[str, Any]
    location: Optional[str] = None
    mood: Optional[str] = None
    alive: bool = True


@dataclass
class EntityProfile:
    """Complete profile of an entity across the narrative."""

    entity: Entity
    states: List[EntityState] = field(default_factory=list)
    behaviors: List[str] = field(default_factory=list)
    first_mention: int = 0
    last_mention: int = 0
    mention_count: int = 0


class EntityTracker:
    """
    Entity tracking engine for behavioral consistency.

    Capabilities:
    - Track entity attributes over time
    - Detect "out of character" behavior
    - Monitor location consistency (no teleportation)
    - Validate relationship consistency
    """

    # Behavior patterns for character archetypes
    ARCHETYPE_BEHAVIORS = {
        "hero": {"brave", "selfless", "determined", "honest"},
        "villain": {"cunning", "selfish", "ruthless", "deceptive"},
        "mentor": {"wise", "patient", "guiding", "experienced"},
        "sidekick": {"loyal", "supportive", "humorous", "brave"},
    }

    # Mood/emotion words
    POSITIVE_MOODS = {"happy", "joyful", "excited", "content", "peaceful", "loving"}
    NEGATIVE_MOODS = {"sad", "angry", "fearful", "anxious", "depressed", "hateful"}

    def __init__(self):
        self._profiles: Dict[UUID, EntityProfile] = {}
        self._name_to_id: Dict[str, UUID] = {}

    async def track_entity(self, entity: Entity, position: int = 0) -> None:
        """Start tracking an entity."""
        if entity.id not in self._profiles:
            profile = EntityProfile(
                entity=entity,
                first_mention=position,
                last_mention=position,
                mention_count=1,
            )
            self._profiles[entity.id] = profile
            self._name_to_id[entity.name.lower()] = entity.id
        else:
            profile = self._profiles[entity.id]
            profile.last_mention = max(profile.last_mention, position)
            profile.mention_count += 1

    async def update_state(
        self,
        entity_id: UUID,
        position: int,
        attributes: Optional[Dict[str, Any]] = None,
        location: Optional[str] = None,
        mood: Optional[str] = None,
        alive: bool = True,
    ) -> None:
        """Update an entity's state at a position in the narrative."""
        if entity_id not in self._profiles:
            return

        state = EntityState(
            entity_id=entity_id,
            position=position,
            attributes=attributes or {},
            location=location,
            mood=mood,
            alive=alive,
        )

        self._profiles[entity_id].states.append(state)
        self._profiles[entity_id].last_mention = position

    async def add_behavior(self, entity_id: UUID, behavior: str) -> None:
        """Record a behavior exhibited by an entity."""
        if entity_id in self._profiles:
            self._profiles[entity_id].behaviors.append(behavior.lower())

    async def check_behavior(
        self, entities: List[Entity], text: str
    ) -> List[ConsistencyIssue]:
        """
        Check for behavioral inconsistencies in the narrative.

        Detects:
        - Sudden personality changes
        - "Out of character" actions
        - Contradictory behaviors
        """
        issues = []

        # Track entities mentioned in this text
        for entity in entities:
            await self.track_entity(entity)

        # Extract behavioral indicators from text
        text_lower = text.lower()

        for entity in entities:
            # Check for behavioral contradictions
            entity_issues = await self._check_entity_behavior(entity, text_lower)
            issues.extend(entity_issues)

            # Check for "resurrection" (dead character acting)
            resurrection_issue = await self._check_alive_status(entity, text)
            if resurrection_issue:
                issues.append(resurrection_issue)

            # Check for impossible locations (teleportation)
            location_issue = await self._check_location_consistency(entity, text)
            if location_issue:
                issues.append(location_issue)

        return issues

    async def _check_entity_behavior(
        self, entity: Entity, text: str
    ) -> List[ConsistencyIssue]:
        """Check if entity's behavior in text is consistent with their profile."""
        issues = []

        if entity.id not in self._profiles:
            return issues

        profile = self._profiles[entity.id]
        entity_name = entity.name.lower()

        # Check if entity name appears in text
        if entity_name not in text:
            return issues

        # Look for behavioral keywords near entity mentions
        # Find sentences mentioning the entity
        sentences = text.split(".")
        entity_sentences = [s for s in sentences if entity_name in s.lower()]

        for sentence in entity_sentences:
            # Check for contradictory moods in same sentence
            has_positive = any(mood in sentence for mood in self.POSITIVE_MOODS)
            has_negative = any(mood in sentence for mood in self.NEGATIVE_MOODS)

            if has_positive and has_negative:
                issues.append(
                    ConsistencyIssue(
                        type=ConstraintType.BEHAVIORAL,
                        level=ConsistencyLevel.WARNING,
                        description=f"Contradictory emotional state for {entity.name}: "
                        f"Both positive and negative moods in same context",
                        evidence=[sentence.strip()],
                        suggested_fix=f"Clarify {entity.name}'s emotional state",
                        confidence=0.6,
                    )
                )

        # Check against established archetype (if any)
        archetype = entity.attributes.get("archetype")
        if archetype and archetype in self.ARCHETYPE_BEHAVIORS:
            expected_behaviors = self.ARCHETYPE_BEHAVIORS[archetype]

            # Check if behavior contradicts archetype
            for sentence in entity_sentences:
                for expected in expected_behaviors:
                    opposite = self._get_opposite_behavior(expected)
                    if opposite and opposite in sentence:
                        issues.append(
                            ConsistencyIssue(
                                type=ConstraintType.BEHAVIORAL,
                                level=ConsistencyLevel.WARNING,
                                description=f"{entity.name} ({archetype}) showing '{opposite}' behavior, "
                                f"which contradicts expected '{expected}' trait",
                                evidence=[sentence.strip()],
                                suggested_fix=f"Either justify the behavioral change or adjust the action",
                                confidence=0.7,
                            )
                        )

        return issues

    def _get_opposite_behavior(self, behavior: str) -> Optional[str]:
        """Get the opposite of a behavior trait."""
        opposites = {
            "brave": "cowardly",
            "selfless": "selfish",
            "honest": "deceptive",
            "cunning": "naive",
            "wise": "foolish",
            "patient": "impatient",
            "loyal": "treacherous",
        }
        return opposites.get(behavior)

    async def _check_alive_status(
        self, entity: Entity, text: str
    ) -> Optional[ConsistencyIssue]:
        """Check if a dead character is acting in the narrative."""
        if entity.id not in self._profiles:
            return None

        profile = self._profiles[entity.id]

        # Check if entity was marked as dead
        for state in profile.states:
            if not state.alive:
                # Entity is dead - check if they're doing things after
                death_position = state.position

                # Check for action verbs after death
                sentences = text.split(".")
                for i, sentence in enumerate(sentences):
                    if i > death_position and entity.name.lower() in sentence.lower():
                        # Check for active verbs
                        action_words = [
                            "walked",
                            "said",
                            "ran",
                            "took",
                            "grabbed",
                            "smiled",
                            "laughed",
                            "fought",
                            "ate",
                            "drank",
                        ]
                        for action in action_words:
                            if action in sentence.lower():
                                return ConsistencyIssue(
                                    type=ConstraintType.BEHAVIORAL,
                                    level=ConsistencyLevel.CRITICAL,
                                    description=f"{entity.name} is performing actions after being marked as dead",
                                    evidence=[
                                        f"Death at position {death_position}",
                                        f"Action at position {i}: '{sentence.strip()[:50]}...'",
                                    ],
                                    suggested_fix=f"Either revive {entity.name} explicitly or change the action",
                                    confidence=0.9,
                                )

        return None

    async def _check_location_consistency(
        self, entity: Entity, text: str
    ) -> Optional[ConsistencyIssue]:
        """Check for impossible location changes (teleportation)."""
        if entity.id not in self._profiles:
            return None

        profile = self._profiles[entity.id]

        # Get location states in order
        location_states = [s for s in profile.states if s.location]

        if len(location_states) < 2:
            return None

        # Check for impossible jumps (far locations with no travel mentioned)
        far_locations = {
            ("paris", "tokyo"),
            ("new york", "london"),
            ("australia", "europe"),
            ("earth", "mars"),
            ("inside", "outside the country"),
        }

        for i in range(1, len(location_states)):
            prev_loc = location_states[i - 1].location.lower()
            curr_loc = location_states[i].location.lower()

            for loc_pair in far_locations:
                if (prev_loc in loc_pair[0] and curr_loc in loc_pair[1]) or (
                    prev_loc in loc_pair[1] and curr_loc in loc_pair[0]
                ):
                    return ConsistencyIssue(
                        type=ConstraintType.SPATIAL,
                        level=ConsistencyLevel.WARNING,
                        description=f"{entity.name} moved from {prev_loc} to {curr_loc} "
                        f"without described travel",
                        evidence=[
                            f"Previous location: {prev_loc} (position {location_states[i-1].position})",
                            f"Current location: {curr_loc} (position {location_states[i].position})",
                        ],
                        suggested_fix=f"Add travel description or adjust timeline",
                        confidence=0.7,
                    )

        return None

    async def get_entity_profile(self, entity_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the complete profile of an entity."""
        if entity_id not in self._profiles:
            return None

        profile = self._profiles[entity_id]
        return {
            "entity": profile.entity.dict(),
            "states": [
                {
                    "position": s.position,
                    "attributes": s.attributes,
                    "location": s.location,
                    "mood": s.mood,
                    "alive": s.alive,
                }
                for s in profile.states
            ],
            "behaviors": profile.behaviors,
            "first_mention": profile.first_mention,
            "last_mention": profile.last_mention,
            "mention_count": profile.mention_count,
        }

    async def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Get profiles for all tracked entities."""
        profiles = []
        for entity_id in self._profiles:
            profile = await self.get_entity_profile(entity_id)
            if profile:
                profiles.append(profile)
        return profiles

    def clear(self) -> None:
        """Clear all tracking data."""
        self._profiles.clear()
        self._name_to_id.clear()
