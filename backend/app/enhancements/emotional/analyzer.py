"""
Emotional Intelligence Analyzer - CONCORD Super Enhancement

Advanced emotional analysis for narrative consistency including:
- Sentiment arc tracking
- Character mood consistency
- Tone uniformity
- Empathy mapping between characters
"""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass, field
import re

from app.models import (
    Entity,
    ConsistencyIssue,
    ConsistencyLevel,
    ConstraintType,
    SentimentType,
)


@dataclass
class CharacterMood:
    """Tracks a character's emotional state at a point."""

    character_name: str
    position: int
    mood: str
    intensity: float  # 0.0 to 1.0
    trigger: Optional[str] = None  # What caused the mood


@dataclass
class EmotionalRelationship:
    """Emotional dynamic between two characters."""

    character1: str
    character2: str
    sentiment: str  # "positive", "negative", "neutral", "complex"
    emotions: List[str] = field(default_factory=list)  # love, hate, fear, trust, etc.


class EmotionalAnalyzer:
    """
    Advanced emotional intelligence analyzer for CONCORD.

    Capabilities:
    - Track individual character emotional arcs
    - Detect jarring mood shifts
    - Validate emotional consistency
    - Map relationships and emotional dynamics
    """

    # Emotion categories with associated words
    EMOTION_LEXICON = {
        "joy": {
            "words": [
                "happy",
                "joyful",
                "elated",
                "cheerful",
                "delighted",
                "ecstatic",
                "thrilled",
                "pleased",
                "content",
            ],
            "intensity_modifiers": {
                "slightly": 0.3,
                "very": 0.8,
                "extremely": 1.0,
                "somewhat": 0.5,
            },
        },
        "sadness": {
            "words": [
                "sad",
                "depressed",
                "melancholy",
                "sorrowful",
                "grief",
                "heartbroken",
                "miserable",
                "gloomy",
                "dejected",
            ],
            "intensity_modifiers": {
                "slightly": 0.3,
                "deeply": 0.9,
                "profoundly": 1.0,
                "somewhat": 0.5,
            },
        },
        "anger": {
            "words": [
                "angry",
                "furious",
                "enraged",
                "irritated",
                "annoyed",
                "outraged",
                "livid",
                "seething",
                "bitter",
            ],
            "intensity_modifiers": {"slightly": 0.3, "extremely": 1.0, "mildly": 0.4},
        },
        "fear": {
            "words": [
                "afraid",
                "scared",
                "terrified",
                "anxious",
                "worried",
                "nervous",
                "panicked",
                "dreading",
                "frightened",
            ],
            "intensity_modifiers": {"slightly": 0.3, "extremely": 1.0, "mortally": 1.0},
        },
        "love": {
            "words": [
                "love",
                "adore",
                "cherish",
                "affection",
                "devoted",
                "enamored",
                "passionate",
                "caring",
                "fond",
            ],
            "intensity_modifiers": {"slightly": 0.3, "deeply": 0.9, "madly": 1.0},
        },
        "disgust": {
            "words": [
                "disgusted",
                "repulsed",
                "revolted",
                "sickened",
                "nauseated",
                "appalled",
                "horrified",
            ],
            "intensity_modifiers": {"slightly": 0.3, "utterly": 1.0},
        },
        "surprise": {
            "words": [
                "surprised",
                "shocked",
                "amazed",
                "astonished",
                "stunned",
                "startled",
                "bewildered",
            ],
            "intensity_modifiers": {"slightly": 0.3, "completely": 1.0},
        },
        "trust": {
            "words": [
                "trust",
                "faith",
                "confidence",
                "belief",
                "reliance",
                "assured",
                "secure",
            ],
            "intensity_modifiers": {"somewhat": 0.5, "completely": 1.0, "blindly": 1.0},
        },
    }

    # Opposing emotions that should trigger warnings if they appear together
    OPPOSING_EMOTIONS = [
        ("joy", "sadness"),
        ("love", "hate"),
        ("trust", "fear"),
        ("anger", "calm"),
    ]

    def __init__(self):
        self._character_moods: Dict[str, List[CharacterMood]] = {}
        self._relationships: List[EmotionalRelationship] = []

    async def analyze_character_emotions(
        self, text: str, entities: List[Entity]
    ) -> Dict[str, Any]:
        """
        Analyze emotional states of characters throughout the narrative.

        Returns:
            {
                "character_arcs": {character_name: [mood_states]},
                "mood_shifts": [detected shifts],
                "emotional_consistency": score,
                "issues": [consistency issues]
            }
        """
        character_names = [e.name for e in entities if e.type.value == "character"]

        # Track moods for each character
        for name in character_names:
            moods = await self._extract_character_moods(text, name)
            self._character_moods[name] = moods

        # Detect mood shifts
        mood_shifts = []
        for name, moods in self._character_moods.items():
            shifts = await self._detect_mood_shifts(name, moods)
            mood_shifts.extend(shifts)

        # Calculate consistency score
        issues = []
        for shift in mood_shifts:
            if shift["severity"] == "jarring":
                issues.append(
                    ConsistencyIssue(
                        type=ConstraintType.BEHAVIORAL,
                        level=ConsistencyLevel.WARNING,
                        description=f"Jarring emotional shift for {shift['character']}: "
                        f"{shift['from_mood']} → {shift['to_mood']} without transition",
                        evidence=[
                            f"At position {shift['from_position']}: {shift['from_mood']}",
                            f"At position {shift['to_position']}: {shift['to_mood']}",
                        ],
                        suggested_fix=f"Add emotional transition or justification for {shift['character']}'s mood change",
                        confidence=shift["confidence"],
                    )
                )

        # Calculate overall consistency score
        if mood_shifts:
            jarring_count = len([s for s in mood_shifts if s["severity"] == "jarring"])
            total_moods = sum(len(m) for m in self._character_moods.values())
            consistency_score = max(0.0, 1.0 - (jarring_count / max(1, total_moods)))
        else:
            consistency_score = 1.0

        return {
            "character_arcs": {
                name: [
                    {
                        "position": m.position,
                        "mood": m.mood,
                        "intensity": m.intensity,
                        "trigger": m.trigger,
                    }
                    for m in moods
                ]
                for name, moods in self._character_moods.items()
            },
            "mood_shifts": mood_shifts,
            "emotional_consistency": consistency_score,
            "issues": issues,
        }

    async def _extract_character_moods(
        self, text: str, character_name: str
    ) -> List[CharacterMood]:
        """Extract mood states for a specific character."""
        moods = []
        sentences = text.split(".")
        name_lower = character_name.lower()

        for pos, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            # Only analyze sentences mentioning the character
            if name_lower not in sentence_lower:
                continue

            # Find emotions in this sentence
            for emotion, data in self.EMOTION_LEXICON.items():
                for word in data["words"]:
                    if word in sentence_lower:
                        # Check for intensity modifiers
                        intensity = 0.6  # Default
                        for modifier, mod_intensity in data[
                            "intensity_modifiers"
                        ].items():
                            if modifier in sentence_lower:
                                intensity = mod_intensity
                                break

                        # Try to find trigger
                        trigger = None
                        trigger_match = re.search(
                            rf"{word}.*?(?:because|due to|after|when)\s+([^.]+)",
                            sentence_lower,
                        )
                        if trigger_match:
                            trigger = trigger_match.group(1).strip()[:50]

                        mood = CharacterMood(
                            character_name=character_name,
                            position=pos,
                            mood=emotion,
                            intensity=intensity,
                            trigger=trigger,
                        )
                        moods.append(mood)
                        break  # One mood per sentence per character

        return moods

    async def _detect_mood_shifts(
        self, character_name: str, moods: List[CharacterMood]
    ) -> List[Dict[str, Any]]:
        """Detect significant mood shifts for a character."""
        shifts = []

        for i in range(1, len(moods)):
            prev_mood = moods[i - 1]
            curr_mood = moods[i]

            # Check if moods are opposing
            is_opposing = False
            for pair in self.OPPOSING_EMOTIONS:
                if (
                    prev_mood.mood in pair
                    and curr_mood.mood in pair
                    and prev_mood.mood != curr_mood.mood
                ):
                    is_opposing = True
                    break

            # Calculate severity
            position_gap = curr_mood.position - prev_mood.position

            if is_opposing and position_gap <= 2:
                severity = "jarring"
                confidence = 0.85
            elif is_opposing and position_gap <= 5:
                severity = "abrupt"
                confidence = 0.7
            elif prev_mood.mood != curr_mood.mood and position_gap == 1:
                severity = "quick"
                confidence = 0.5
            else:
                continue  # Not significant

            shifts.append(
                {
                    "character": character_name,
                    "from_mood": prev_mood.mood,
                    "from_position": prev_mood.position,
                    "from_intensity": prev_mood.intensity,
                    "to_mood": curr_mood.mood,
                    "to_position": curr_mood.position,
                    "to_intensity": curr_mood.intensity,
                    "severity": severity,
                    "confidence": confidence,
                    "trigger": curr_mood.trigger,
                }
            )

        return shifts

    async def analyze_relationships(
        self, text: str, entities: List[Entity]
    ) -> List[EmotionalRelationship]:
        """
        Analyze emotional relationships between characters.
        """
        character_names = [e.name for e in entities if e.type.value == "character"]
        relationships = []

        # Find co-mentions and emotional context
        sentences = text.split(".")

        for i, char1 in enumerate(character_names):
            for char2 in character_names[i + 1 :]:
                # Find sentences mentioning both
                shared_sentences = [
                    s
                    for s in sentences
                    if char1.lower() in s.lower() and char2.lower() in s.lower()
                ]

                if not shared_sentences:
                    continue

                # Analyze emotional tone
                emotions = []
                overall_sentiment = "neutral"

                for sentence in shared_sentences:
                    sentence_lower = sentence.lower()

                    # Check for relationship indicators
                    if any(
                        w in sentence_lower
                        for w in ["love", "loves", "adores", "cherish"]
                    ):
                        emotions.append("love")
                    if any(
                        w in sentence_lower
                        for w in ["hate", "hates", "despise", "loathe"]
                    ):
                        emotions.append("hate")
                    if any(
                        w in sentence_lower
                        for w in ["trust", "trusts", "believe", "rely"]
                    ):
                        emotions.append("trust")
                    if any(
                        w in sentence_lower
                        for w in ["fear", "fears", "afraid", "scared"]
                    ):
                        emotions.append("fear")
                    if any(
                        w in sentence_lower for w in ["friend", "friends", "friendship"]
                    ):
                        emotions.append("friendship")
                    if any(w in sentence_lower for w in ["enemy", "enemies", "rival"]):
                        emotions.append("rivalry")

                # Determine overall sentiment
                positive_emotions = {"love", "trust", "friendship"}
                negative_emotions = {"hate", "fear", "rivalry"}

                pos_count = len([e for e in emotions if e in positive_emotions])
                neg_count = len([e for e in emotions if e in negative_emotions])

                if pos_count > neg_count:
                    overall_sentiment = "positive"
                elif neg_count > pos_count:
                    overall_sentiment = "negative"
                elif pos_count > 0 and neg_count > 0:
                    overall_sentiment = "complex"

                relationship = EmotionalRelationship(
                    character1=char1,
                    character2=char2,
                    sentiment=overall_sentiment,
                    emotions=list(set(emotions)),
                )
                relationships.append(relationship)
                self._relationships.append(relationship)

        return relationships

    async def check_tone_consistency(self, text: str) -> Dict[str, Any]:
        """
        Check overall tone consistency of the narrative.

        Returns analysis of narrative tone and any inconsistencies.
        """
        sentences = text.split(".")
        tones = []

        formal_words = {"therefore", "however", "moreover", "thus", "hereby", "whereby"}
        informal_words = {"gonna", "wanna", "kinda", "sorta", "yeah", "nope", "stuff"}
        dark_words = {
            "death",
            "murder",
            "blood",
            "darkness",
            "horror",
            "terror",
            "doom",
        }
        light_words = {
            "sunshine",
            "rainbow",
            "laughter",
            "play",
            "dance",
            "joy",
            "bright",
        }

        for pos, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            # Determine tone of this sentence
            is_formal = any(w in sentence_lower for w in formal_words)
            is_informal = any(w in sentence_lower for w in informal_words)
            is_dark = any(w in sentence_lower for w in dark_words)
            is_light = any(w in sentence_lower for w in light_words)

            if is_formal and is_informal:
                tone = "mixed_formality"
            elif is_dark and is_light:
                tone = "mixed_mood"
            elif is_formal:
                tone = "formal"
            elif is_informal:
                tone = "informal"
            elif is_dark:
                tone = "dark"
            elif is_light:
                tone = "light"
            else:
                tone = "neutral"

            tones.append({"position": pos, "tone": tone})

        # Detect inconsistencies
        inconsistencies = []
        for i in range(1, len(tones)):
            if tones[i]["tone"].startswith("mixed"):
                inconsistencies.append(
                    {
                        "position": tones[i]["position"],
                        "issue": f"Mixed tone detected: {tones[i]['tone']}",
                    }
                )
            elif (
                tones[i - 1]["tone"] in ["formal", "informal"]
                and tones[i]["tone"] in ["formal", "informal"]
                and tones[i - 1]["tone"] != tones[i]["tone"]
            ):
                inconsistencies.append(
                    {
                        "position": tones[i]["position"],
                        "issue": f"Formality shift: {tones[i-1]['tone']} → {tones[i]['tone']}",
                    }
                )

        # Calculate consistency score
        if tones:
            inconsistency_ratio = len(inconsistencies) / len(tones)
            consistency_score = max(0.0, 1.0 - (inconsistency_ratio * 2))
        else:
            consistency_score = 1.0

        return {
            "tones": tones,
            "inconsistencies": inconsistencies,
            "consistency_score": consistency_score,
            "dominant_tone": (
                max(
                    set(t["tone"] for t in tones),
                    key=lambda x: sum(1 for t in tones if t["tone"] == x),
                )
                if tones
                else "neutral"
            ),
        }

    def clear(self) -> None:
        """Clear all tracked data."""
        self._character_moods.clear()
        self._relationships.clear()
