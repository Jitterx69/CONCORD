"""
Temporal Reasoner - Core CONCORD Component

Ensures timeline consistency and proper causality in narratives.
Validates event sequences, durations, and cause-effect relationships.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import re
from dataclasses import dataclass

from app.models import (
    Fact,
    ConsistencyIssue,
    ConsistencyLevel,
    ConstraintType,
)


@dataclass
class TemporalEvent:
    """Represents a temporal event in the narrative."""

    id: UUID
    description: str
    position: int  # Position in text
    timestamp: Optional[datetime] = None
    relative_time: Optional[str] = None  # "before", "after", "during", etc.
    reference_event_id: Optional[UUID] = None
    duration: Optional[timedelta] = None


@dataclass
class TimelineEntry:
    """Entry in the narrative timeline."""

    event: TemporalEvent
    order: int
    confidence: float


class TemporalReasoner:
    """
    Temporal reasoning engine for narrative consistency.

    Capabilities:
    - Event sequencing validation
    - Cause-effect verification
    - Duration and interval checking
    - Timeline extraction
    """

    # Temporal markers in text
    BEFORE_MARKERS = ["before", "prior to", "earlier", "previously", "ago", "used to"]
    AFTER_MARKERS = ["after", "following", "later", "subsequently", "then", "next"]
    DURING_MARKERS = ["during", "while", "as", "meanwhile", "at the same time"]

    # Time expressions
    TIME_PATTERNS = [
        r"(\d+)\s*(years?|months?|weeks?|days?|hours?|minutes?)\s*(ago|later|before|after)",
        r"(yesterday|today|tomorrow|last\s+\w+|next\s+\w+)",
        r"(in\s+the\s+morning|in\s+the\s+evening|at\s+night|at\s+noon)",
        r"(\d{1,2}:\d{2}(?:\s*[AP]M)?)",
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,?\s+\d{4})?",
    ]

    def __init__(self):
        self._events: Dict[UUID, TemporalEvent] = {}
        self._timeline: List[TimelineEntry] = []

    async def check_timeline(self, text: str, facts: List[Fact]) -> List[ConsistencyIssue]:
        """
        Check temporal consistency of narrative text.

        Detects:
        - Events happening before they're caused
        - Impossible time jumps
        - Contradictory temporal references
        """
        issues = []

        # Extract temporal events from text
        events = await self._extract_events(text)

        # Build timeline
        timeline = await self._build_timeline(events)

        # Check for temporal inconsistencies
        for i, entry in enumerate(timeline):
            # Check against subsequent events
            for j in range(i + 1, len(timeline)):
                next_entry = timeline[j]

                # Check if temporal order is violated
                violation = await self._check_temporal_order(entry, next_entry, text)
                if violation:
                    issues.append(violation)

        # Check for cause-effect violations
        causal_issues = await self._check_causality(text, facts)
        issues.extend(causal_issues)

        # Check for impossible durations
        duration_issues = await self._check_durations(text)
        issues.extend(duration_issues)

        return issues

    async def _extract_events(self, text: str) -> List[TemporalEvent]:
        """Extract temporal events from narrative text."""
        events = []
        sentences = text.split(".")

        for pos, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check for temporal markers
            has_temporal = False
            relative_time = None

            sentence_lower = sentence.lower()

            for marker in self.BEFORE_MARKERS:
                if marker in sentence_lower:
                    has_temporal = True
                    relative_time = "before"
                    break

            if not relative_time:
                for marker in self.AFTER_MARKERS:
                    if marker in sentence_lower:
                        has_temporal = True
                        relative_time = "after"
                        break

            if not relative_time:
                for marker in self.DURING_MARKERS:
                    if marker in sentence_lower:
                        has_temporal = True
                        relative_time = "during"
                        break

            # Check for time expressions
            timestamp = None
            for pattern in self.TIME_PATTERNS:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    has_temporal = True
                    # Parse timestamp if possible (simplified)
                    break

            if has_temporal or pos == 0:  # Always include first sentence as anchor
                event = TemporalEvent(
                    id=uuid4(), description=sentence, position=pos, relative_time=relative_time
                )
                events.append(event)
                self._events[event.id] = event

        return events

    async def _build_timeline(self, events: List[TemporalEvent]) -> List[TimelineEntry]:
        """Build a chronological timeline from events."""
        timeline = []

        for i, event in enumerate(events):
            entry = TimelineEntry(
                event=event, order=i, confidence=0.8 if event.relative_time else 0.6
            )
            timeline.append(entry)

        self._timeline = timeline
        return timeline

    async def _check_temporal_order(
        self, earlier: TimelineEntry, later: TimelineEntry, text: str
    ) -> Optional[ConsistencyIssue]:
        """Check if temporal order between two events is violated."""

        # Check for "before" references that contradict order
        if later.event.relative_time == "before":
            # This event claims to be "before" something, but appears later in text
            # Check if it references the earlier event
            if self._references_event(later.event.description, earlier.event.description):
                return ConsistencyIssue(
                    type=ConstraintType.TEMPORAL,
                    level=ConsistencyLevel.WARNING,
                    description=f"Potential temporal inconsistency: Event at position {later.event.position} "
                    f"claims to be 'before' an event mentioned earlier at position {earlier.event.position}",
                    evidence=[
                        f"Earlier mention: '{earlier.event.description[:50]}...'",
                        f"Later 'before' reference: '{later.event.description[:50]}...'",
                    ],
                    position=later.event.position,
                    confidence=0.7,
                )

        return None

    def _references_event(self, text1: str, text2: str) -> bool:
        """Check if text1 references content from text2."""
        # Simple word overlap check
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Filter common words
        common_words = {"the", "a", "an", "is", "was", "were", "are", "he", "she", "it", "they"}
        words1 -= common_words
        words2 -= common_words

        overlap = words1 & words2
        return len(overlap) >= 2

    async def _check_causality(self, text: str, facts: List[Fact]) -> List[ConsistencyIssue]:
        """Check for cause-effect violations."""
        issues = []

        # Look for causal patterns
        causal_patterns = [
            r"because\s+(.+?),\s*(.+)",
            r"(.+)\s+caused\s+(.+)",
            r"(.+)\s+resulted\s+in\s+(.+)",
            r"(.+)\s+led\s+to\s+(.+)",
            r"as\s+a\s+result\s+of\s+(.+?),\s*(.+)",
        ]

        sentences = text.split(".")

        for pattern in causal_patterns:
            for i, sentence in enumerate(sentences):
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    # Found a causal claim - check if cause appears before effect
                    cause = match.group(1)
                    effect = match.group(2) if len(match.groups()) > 1 else ""

                    # Check if effect was mentioned before cause in the narrative
                    cause_first_pos = text.lower().find(cause.lower()[:20])
                    effect_first_pos = text.lower().find(effect.lower()[:20]) if effect else -1

                    if effect_first_pos != -1 and effect_first_pos < cause_first_pos:
                        issues.append(
                            ConsistencyIssue(
                                type=ConstraintType.CAUSAL,
                                level=ConsistencyLevel.WARNING,
                                description=f"Effect mentioned before its cause in the narrative",
                                evidence=[
                                    f"Cause: '{cause[:50]}...'",
                                    f"Effect: '{effect[:50]}...'",
                                ],
                                position=i,
                                confidence=0.6,
                            )
                        )

        return issues

    async def _check_durations(self, text: str) -> List[ConsistencyIssue]:
        """Check for impossible or contradictory durations."""
        issues = []

        # Pattern for duration statements
        duration_pattern = r"for\s+(\d+)\s+(years?|months?|weeks?|days?|hours?|minutes?)"

        durations = []
        for match in re.finditer(duration_pattern, text, re.IGNORECASE):
            amount = int(match.group(1))
            unit = match.group(2).lower()
            position = match.start()
            durations.append((amount, unit, position))

        # Check for impossible durations (e.g., 1000 years ago for a living character)
        for amount, unit, pos in durations:
            if unit.startswith("year") and amount > 150:
                issues.append(
                    ConsistencyIssue(
                        type=ConstraintType.TEMPORAL,
                        level=ConsistencyLevel.WARNING,
                        description=f"Unusually long duration: {amount} {unit}. "
                        f"This may be inconsistent with character lifespans.",
                        evidence=[f"Duration: {amount} {unit}"],
                        position=pos,
                        suggested_fix="Verify this duration is intentional for the narrative context",
                        confidence=0.5,
                    )
                )

        return issues

    async def extract_timeline(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract a visualization-friendly timeline from narrative text.
        """
        events = await self._extract_events(text)
        timeline = await self._build_timeline(events)

        return [
            {
                "id": str(entry.event.id),
                "order": entry.order,
                "description": entry.event.description,
                "position": entry.event.position,
                "relative_time": entry.event.relative_time,
                "confidence": entry.confidence,
            }
            for entry in timeline
        ]

    def clear(self) -> None:
        """Clear all temporal data."""
        self._events.clear()
        self._timeline.clear()
