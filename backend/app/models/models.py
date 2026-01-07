"""
Data Models for CONCORD
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


# ============== Enums ==============

class EntityType(str, Enum):
    """Types of entities in a narrative"""
    CHARACTER = "character"
    LOCATION = "location"
    OBJECT = "object"
    EVENT = "event"
    CONCEPT = "concept"
    TIME = "time"


class ConstraintType(str, Enum):
    """Types of constraints for consistency checking"""
    FACTUAL = "factual"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    SPATIAL = "spatial"
    BEHAVIORAL = "behavioral"
    RELATIONAL = "relational"


class ConsistencyLevel(str, Enum):
    """Consistency check result levels"""
    CONSISTENT = "consistent"
    WARNING = "warning"
    INCONSISTENT = "inconsistent"
    CRITICAL = "critical"


class SentimentType(str, Enum):
    """Sentiment categories for emotional analysis"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


# ============== Entity Models ==============

class Entity(BaseModel):
    """Represents an entity in the narrative"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: EntityType
    attributes: Dict[str, Any] = Field(default_factory=dict)
    first_appearance: Optional[int] = None  # Line/position of first mention
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice",
                "type": "character",
                "attributes": {"age": 25, "occupation": "detective", "hair_color": "brown"}
            }
        }


class Relationship(BaseModel):
    """Represents a relationship between entities"""
    id: UUID = Field(default_factory=uuid4)
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    established_at: Optional[int] = None  # Position where relationship was established
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_entity_id": "uuid-1",
                "target_entity_id": "uuid-2",
                "relationship_type": "friend_of",
                "properties": {"since": "childhood"}
            }
        }


# ============== Constraint Models ==============

class Constraint(BaseModel):
    """Represents a constraint/fact in the narrative"""
    id: UUID = Field(default_factory=uuid4)
    type: ConstraintType
    description: str
    entity_ids: List[UUID] = Field(default_factory=list)
    rule: str  # The actual constraint rule
    is_hard: bool = True  # Hard constraints must be satisfied; soft can be relaxed
    priority: int = Field(default=5, ge=1, le=10)
    source_position: Optional[int] = None  # Where this constraint was established
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "factual",
                "description": "Alice is 25 years old",
                "rule": "entity.Alice.age == 25",
                "is_hard": True,
                "priority": 8
            }
        }


class Fact(BaseModel):
    """Represents an established fact in the narrative"""
    id: UUID = Field(default_factory=uuid4)
    subject: str
    predicate: str
    object: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_text: Optional[str] = None
    position: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Alice",
                "predicate": "has_occupation",
                "object": "detective",
                "confidence": 1.0,
                "source_text": "Alice worked as a detective for ten years."
            }
        }


# ============== Narrative Models ==============

class NarrativeSegment(BaseModel):
    """A segment/chunk of narrative text"""
    id: UUID = Field(default_factory=uuid4)
    text: str
    position: int  # Order in the narrative
    entities_mentioned: List[UUID] = Field(default_factory=list)
    facts_established: List[UUID] = Field(default_factory=list)
    
    
class Narrative(BaseModel):
    """Complete narrative with metadata"""
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    segments: List[NarrativeSegment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Mystery of the Old Manor",
                "description": "A detective story set in Victorian England"
            }
        }


# ============== Consistency Models ==============

class ConsistencyIssue(BaseModel):
    """Represents a detected consistency issue"""
    id: UUID = Field(default_factory=uuid4)
    type: ConstraintType
    level: ConsistencyLevel
    description: str
    conflicting_facts: List[UUID] = Field(default_factory=list)
    position: Optional[int] = None
    evidence: List[str] = Field(default_factory=list)
    suggested_fix: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ConsistencyReport(BaseModel):
    """Complete consistency analysis report"""
    id: UUID = Field(default_factory=uuid4)
    narrative_id: UUID
    overall_score: float = Field(ge=0.0, le=1.0)
    level: ConsistencyLevel
    issues: List[ConsistencyIssue] = Field(default_factory=list)
    facts_checked: int = 0
    constraints_validated: int = 0
    entities_tracked: int = 0
    analysis_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Breakdown by category
    factual_score: float = Field(default=1.0, ge=0.0, le=1.0)
    temporal_score: float = Field(default=1.0, ge=0.0, le=1.0)
    causal_score: float = Field(default=1.0, ge=0.0, le=1.0)
    spatial_score: float = Field(default=1.0, ge=0.0, le=1.0)
    behavioral_score: float = Field(default=1.0, ge=0.0, le=1.0)
    relational_score: float = Field(default=1.0, ge=0.0, le=1.0)


# ============== Emotional Analysis Models ==============

class EmotionalState(BaseModel):
    """Emotional state at a point in the narrative"""
    sentiment: SentimentType
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    emotions: Dict[str, float] = Field(default_factory=dict)  # emotion -> intensity
    tone: Optional[str] = None
    position: int


class EmotionalArc(BaseModel):
    """Emotional trajectory over the narrative"""
    narrative_id: UUID
    states: List[EmotionalState] = Field(default_factory=list)
    overall_sentiment: SentimentType
    tone_consistency_score: float = Field(ge=0.0, le=1.0)
    arc_pattern: Optional[str] = None  # e.g., "rising", "falling", "arc"


# ============== Request/Response Models ==============

class ConsistencyCheckRequest(BaseModel):
    """Request to check narrative consistency"""
    text: str
    existing_facts: Optional[List[Fact]] = None
    check_emotional: bool = True
    check_temporal: bool = True
    auto_fix: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Alice walked into the room. She was 25 years old. Later, Alice mentioned she had just turned 30.",
                "check_emotional": True,
                "check_temporal": True,
                "auto_fix": False
            }
        }


class ConsistencyCheckResponse(BaseModel):
    """Response from consistency check"""
    report: ConsistencyReport
    emotional_arc: Optional[EmotionalArc] = None
    suggested_fixes: List[str] = Field(default_factory=list)
    processing_time_ms: float


class AddFactRequest(BaseModel):
    """Request to add a fact to knowledge graph"""
    subject: str
    predicate: str
    object: str
    source_text: Optional[str] = None


class NarrativeCreateRequest(BaseModel):
    """Request to create a new narrative"""
    title: str
    description: Optional[str] = None
    initial_text: Optional[str] = None


class NarrativeUpdateRequest(BaseModel):
    """Request to update/append to narrative"""
    text: str
    position: Optional[int] = None  # Position to insert; None = append
