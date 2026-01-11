"""
ML Service - Core NLP and AI functionality for CONCORD

Provides entity extraction, fact extraction, sentiment analysis,
and natural language query processing.
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
import re
import asyncio

from app.models import (
    Entity,
    EntityType,
    Fact,
    EmotionalArc,
    EmotionalState,
    SentimentType,
)
from app.config import settings


class MLService:
    """
    Machine Learning service for CONCORD.

    In production, this would integrate with:
    - Hugging Face Transformers for NLP
    - spaCy for NER
    - Sentence Transformers for embeddings
    - Custom fine-tuned models

    This implementation provides functional heuristic-based
    processing for demonstration without heavy dependencies.
    """

    # Named Entity Recognition patterns
    ENTITY_PATTERNS = {
        EntityType.CHARACTER: [
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:said|walked|ran|looked|thought|felt|was|is|are|were)",
            r"\b(Dr\.|Mr\.|Mrs\.|Ms\.|Professor)\s+([A-Z][a-z]+)",
            r"(?:he|she|they)\s+called\s+([A-Z][a-z]+)",
        ],
        EntityType.LOCATION: [
            r"(?:in|at|to|from)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:city|town|village|country|land)\s+of\s+([A-Z][a-z]+)",
        ],
        EntityType.OBJECT: [
            r"(?:the|a|an)\s+(ancient|magical|golden|silver|old|new)\s+(\w+)",
        ],
        EntityType.TIME: [
            r"(morning|evening|night|noon|midnight|dawn|dusk)",
            r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}",
        ],
    }

    # Fact extraction patterns (Subject-Predicate-Object)
    FACT_PATTERNS = [
        r"([A-Z][a-z]+)\s+(?:is|was|are|were)\s+(?:a|an|the)?\s*(\w+)",  # X is/was Y
        r"([A-Z][a-z]+)\s+(?:has|had|have)\s+(\w+)\s+(\w+)",  # X has Y Z
        r"([A-Z][a-z]+)\s+(?:works?|worked)\s+(?:as|at)\s+(?:a|an|the)?\s*([^.]+)",  # X works as Y
        r"([A-Z][a-z]+)(?:'s|'s)\s+(\w+)\s+(?:is|was|are|were)\s+([^.]+)",  # X's Y is Z
        r"([A-Z][a-z]+)\s+(?:is|was)\s+(\d+)\s+years?\s+old",  # X is N years old
    ]

    # Sentiment words
    POSITIVE_WORDS = {
        "happy",
        "joy",
        "love",
        "wonderful",
        "amazing",
        "great",
        "excellent",
        "beautiful",
        "peaceful",
        "delighted",
        "excited",
        "thrilled",
        "grateful",
        "hopeful",
        "cheerful",
        "pleased",
        "satisfied",
        "content",
        "blessed",
    }

    NEGATIVE_WORDS = {
        "sad",
        "angry",
        "hate",
        "terrible",
        "awful",
        "horrible",
        "disgusting",
        "fearful",
        "anxious",
        "depressed",
        "miserable",
        "upset",
        "frustrated",
        "disappointed",
        "heartbroken",
        "devastated",
        "worried",
        "scared",
    }

    def __init__(self):
        self._initialized = False
        self._models = {}

    async def initialize(self) -> None:
        """Initialize ML models."""
        # In production, load actual models here
        # For now, we use heuristic-based processing
        self._initialized = True
        print("📦 ML Service initialized (heuristic mode)")

    async def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract named entities from text.

        Returns a list of Entity objects with type and attributes.
        """
        entities = []
        seen_names = set()

        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    # Get the matched name
                    name = match.group(1) if match.lastindex >= 1 else match.group(0)
                    name = name.strip()

                    # Skip if too short or already seen
                    if len(name) < 2 or name.lower() in seen_names:
                        continue

                    seen_names.add(name.lower())

                    entity = Entity(
                        id=uuid4(),
                        name=name,
                        type=entity_type,
                        attributes={},
                        first_appearance=match.start(),
                    )
                    entities.append(entity)

        # Try to extract attributes for characters
        for entity in entities:
            if entity.type == EntityType.CHARACTER:
                entity.attributes = await self._extract_character_attributes(
                    text, entity.name
                )

        return entities

    async def _extract_character_attributes(
        self, text: str, name: str
    ) -> Dict[str, Any]:
        """Extract attributes for a character from text."""
        attributes = {}
        name_lower = name.lower()

        # Age pattern
        age_match = re.search(
            rf"{name}\s+(?:is|was)\s+(\d+)\s+years?\s+old", text, re.IGNORECASE
        )
        if age_match:
            attributes["age"] = int(age_match.group(1))

        # Occupation pattern
        occ_match = re.search(
            rf"{name}\s+(?:is|was|works?|worked)\s+(?:as\s+)?(?:a|an|the)?\s*(\w+(?:\s+\w+)?)",
            text,
            re.IGNORECASE,
        )
        if occ_match:
            occupation = occ_match.group(1).strip()
            if occupation.lower() not in {"a", "an", "the", name_lower}:
                attributes["occupation"] = occupation

        # Physical description
        desc_patterns = {
            "hair_color": rf"{name}(?:'s)?\s+(\w+)\s+hair",
            "eye_color": rf"{name}(?:'s)?\s+(\w+)\s+eyes?",
            "height": rf"{name}\s+(?:is|was)\s+(tall|short|average)",
        }

        for attr, pattern in desc_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                attributes[attr] = match.group(1).lower()

        return attributes

    async def extract_facts(self, text: str) -> List[Fact]:
        """
        Extract facts (subject-predicate-object triples) from text.
        """
        facts = []
        sentences = text.split(".")

        for pos, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue

            # Try each fact pattern
            for pattern in self.FACT_PATTERNS:
                for match in re.finditer(pattern, sentence, re.IGNORECASE):
                    groups = match.groups()

                    if len(groups) >= 2:
                        subject = groups[0].strip()

                        # Determine predicate and object based on pattern
                        if len(groups) == 2:
                            predicate = "is"
                            obj = groups[1].strip()
                        elif len(groups) >= 3:
                            predicate = groups[1].strip()
                            obj = groups[2].strip() if len(groups) > 2 else ""
                        else:
                            continue

                        # Skip low-quality extractions
                        if len(subject) < 2 or len(obj) < 2:
                            continue

                        fact = Fact(
                            id=uuid4(),
                            subject=subject,
                            predicate=predicate,
                            object=obj,
                            source_text=sentence[:100],
                            position=pos,
                            confidence=0.8,
                        )
                        facts.append(fact)

        return facts

    async def analyze_emotional_arc(self, text: str) -> EmotionalArc:
        """
        Analyze the emotional arc of the narrative.

        Tracks sentiment changes throughout the text.
        """
        states = []
        sentences = text.split(".")

        overall_positive = 0
        overall_negative = 0

        for pos, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            # Count sentiment words
            positive_count = sum(
                1 for word in self.POSITIVE_WORDS if word in sentence_lower
            )
            negative_count = sum(
                1 for word in self.NEGATIVE_WORDS if word in sentence_lower
            )

            overall_positive += positive_count
            overall_negative += negative_count

            # Calculate sentiment score (-1 to 1)
            total = positive_count + negative_count
            if total > 0:
                score = (positive_count - negative_count) / total
            else:
                score = 0.0

            # Determine sentiment type
            if score > 0.2:
                sentiment = SentimentType.POSITIVE
            elif score < -0.2:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL

            # Find specific emotions
            emotions = {}
            emotion_words = {
                "joy": ["happy", "joy", "delighted", "thrilled"],
                "sadness": ["sad", "depressed", "miserable", "heartbroken"],
                "anger": ["angry", "furious", "enraged", "frustrated"],
                "fear": ["scared", "afraid", "terrified", "anxious"],
                "love": ["love", "affection", "adore", "cherish"],
            }

            for emotion, words in emotion_words.items():
                if any(w in sentence_lower for w in words):
                    emotions[emotion] = 0.8

            state = EmotionalState(
                sentiment=sentiment,
                sentiment_score=score,
                emotions=emotions,
                position=pos,
            )
            states.append(state)

        # Determine overall sentiment
        if overall_positive > overall_negative * 1.5:
            overall = SentimentType.POSITIVE
        elif overall_negative > overall_positive * 1.5:
            overall = SentimentType.NEGATIVE
        else:
            overall = SentimentType.NEUTRAL

        # Calculate tone consistency
        # (how much does sentiment vary?)
        if len(states) > 1:
            scores = [s.sentiment_score for s in states if s.sentiment_score != 0]
            if scores:
                variance = sum(
                    (s - sum(scores) / len(scores)) ** 2 for s in scores
                ) / len(scores)
                tone_consistency = max(0.0, 1.0 - variance)
            else:
                tone_consistency = 1.0
        else:
            tone_consistency = 1.0

        # Determine arc pattern
        if len(states) >= 3:
            first_third = sum(s.sentiment_score for s in states[: len(states) // 3])
            last_third = sum(s.sentiment_score for s in states[-len(states) // 3 :])

            if last_third > first_third + 0.5:
                arc_pattern = "rising"
            elif last_third < first_third - 0.5:
                arc_pattern = "falling"
            elif abs(last_third - first_third) < 0.3:
                arc_pattern = "flat"
            else:
                arc_pattern = "arc"
        else:
            arc_pattern = "flat"

        return EmotionalArc(
            narrative_id=uuid4(),  # Would be real narrative ID
            states=states,
            overall_sentiment=overall,
            tone_consistency_score=tone_consistency,
            arc_pattern=arc_pattern,
        )

    async def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query into structured format.

        Example queries:
        - "What is Alice's occupation?" -> {type: "attribute", subject: "Alice", predicate: "occupation"}
        - "Who is friends with Bob?" -> {type: "relationship", subject: "Bob", predicate: "friends"}
        """
        query_lower = query.lower()

        # "What is X's Y?" pattern
        what_is_match = re.search(
            r"what\s+(?:is|are|was|were)\s+(\w+)(?:'s|s')?\s+(\w+)", query_lower
        )
        if what_is_match:
            return {
                "type": "attribute",
                "subject": what_is_match.group(1).title(),
                "predicate": what_is_match.group(2),
            }

        # "Who is X?" pattern
        who_is_match = re.search(r"who\s+(?:is|are|was|were)\s+(\w+)", query_lower)
        if who_is_match:
            return {"type": "exists", "subject": who_is_match.group(1).title()}

        # "Does X exist?" pattern
        exists_match = re.search(
            r"(?:does|is)\s+(\w+)\s+(?:exist|mentioned)", query_lower
        )
        if exists_match:
            return {"type": "exists", "subject": exists_match.group(1).title()}

        # "Who is friends with X?" relationship pattern
        rel_match = re.search(
            r"who\s+(?:is|are|was|were)\s+(\w+)\s+(?:with|of|to)\s+(\w+)", query_lower
        )
        if rel_match:
            return {
                "type": "relationship",
                "subject": rel_match.group(2).title(),
                "predicate": rel_match.group(1),
            }

        # Default: treat as subject search
        words = [w for w in query.split() if len(w) > 2 and w[0].isupper()]
        if words:
            return {"type": "attribute", "subject": words[0]}

        return {"type": "attribute", "subject": query}

    async def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts.

        In production, this would use sentence transformers.
        This implementation uses word overlap (Jaccard similarity).
        """
        # Tokenize
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Remove stopwords
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "was",
            "were",
            "are",
            "in",
            "on",
            "at",
            "to",
            "for",
        }
        words1 -= stopwords
        words2 -= stopwords

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0
