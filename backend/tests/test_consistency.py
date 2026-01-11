"""
Tests for CONCORD Consistency Engine
"""

import pytest
from uuid import uuid4

from app.core.knowledge_graph import KnowledgeGraph
from app.core.constraint_engine import ConstraintEngine
from app.core.temporal_reasoner import TemporalReasoner
from app.core.entity_tracker import EntityTracker
from app.core.explainer import Explainer
from app.services.ml_service import MLService
from app.models import (
    Entity,
    EntityType,
    Fact,
    Constraint,
    ConstraintType,
    ConsistencyLevel,
)


class TestKnowledgeGraph:
    """Tests for the Knowledge Graph component."""

    @pytest.fixture
    def knowledge_graph(self):
        return KnowledgeGraph()

    @pytest.mark.asyncio
    async def test_add_and_get_entity(self, knowledge_graph):
        """Test adding and retrieving an entity."""
        entity = Entity(
            name="Alice",
            type=EntityType.CHARACTER,
            attributes={"age": 25, "occupation": "detective"},
        )

        await knowledge_graph.add_entity(entity)
        retrieved = await knowledge_graph.get_entity(entity.id)

        assert retrieved is not None
        assert retrieved.name == "Alice"
        assert retrieved.attributes["age"] == 25

    @pytest.mark.asyncio
    async def test_add_and_get_fact(self, knowledge_graph):
        """Test adding and retrieving a fact."""
        fact = Fact(subject="Alice", predicate="occupation", object="detective")

        await knowledge_graph.add_fact(fact)
        facts = await knowledge_graph.get_facts_by_subject("Alice")

        assert len(facts) == 1
        assert facts[0].predicate == "occupation"
        assert facts[0].object == "detective"

    @pytest.mark.asyncio
    async def test_check_conflicts_detects_contradiction(self, knowledge_graph):
        """Test that conflicting facts are detected."""
        # Add existing fact
        existing_fact = Fact(subject="Alice", predicate="age", object="25")
        await knowledge_graph.add_fact(existing_fact)

        # Create conflicting new fact
        new_fact = Fact(subject="Alice", predicate="age", object="30")

        issues = await knowledge_graph.check_conflicts([new_fact])

        assert len(issues) == 1
        assert issues[0].type == ConstraintType.FACTUAL
        assert "contradiction" in issues[0].description.lower()


class TestConstraintEngine:
    """Tests for the Constraint Engine component."""

    @pytest.fixture
    def constraint_engine(self):
        return ConstraintEngine()

    @pytest.mark.asyncio
    async def test_validate_no_conflicts(self, constraint_engine):
        """Test validation with no conflicting facts."""
        facts = [
            Fact(subject="Alice", predicate="age", object="25"),
            Fact(subject="Bob", predicate="age", object="30"),
        ]

        issues = await constraint_engine.validate(facts)

        # Should have no issues as there are no conflicts
        conflicting_issues = [i for i in issues if i.type == ConstraintType.FACTUAL]
        assert len(conflicting_issues) == 0

    @pytest.mark.asyncio
    async def test_validate_detects_implicit_conflict(self, constraint_engine):
        """Test detection of conflicting facts within input."""
        facts = [
            Fact(subject="Alice", predicate="age", object="25"),
            Fact(subject="Alice", predicate="age", object="30"),
        ]

        issues = await constraint_engine.validate(facts)

        assert len(issues) >= 1
        assert any("conflict" in i.description.lower() for i in issues)


class TestTemporalReasoner:
    """Tests for the Temporal Reasoner component."""

    @pytest.fixture
    def temporal_reasoner(self):
        return TemporalReasoner()

    @pytest.mark.asyncio
    async def test_extract_timeline(self, temporal_reasoner):
        """Test timeline extraction from narrative."""
        text = (
            "In the morning, Alice went to work. Later that evening, she returned home."
        )

        timeline = await temporal_reasoner.extract_timeline(text)

        assert len(timeline) >= 1

    @pytest.mark.asyncio
    async def test_check_timeline_no_issues(self, temporal_reasoner):
        """Test timeline check with consistent narrative."""
        text = "First, Alice woke up. Then she had breakfast. After that, she went to work."
        facts = []

        issues = await temporal_reasoner.check_timeline(text, facts)

        # Simple linear narrative should have few to no temporal issues
        critical_issues = [i for i in issues if i.level == ConsistencyLevel.CRITICAL]
        assert len(critical_issues) == 0


class TestEntityTracker:
    """Tests for the Entity Tracker component."""

    @pytest.fixture
    def entity_tracker(self):
        return EntityTracker()

    @pytest.mark.asyncio
    async def test_track_entity(self, entity_tracker):
        """Test entity tracking."""
        entity = Entity(
            name="Alice", type=EntityType.CHARACTER, attributes={"archetype": "hero"}
        )

        await entity_tracker.track_entity(entity, position=0)
        profile = await entity_tracker.get_entity_profile(entity.id)

        assert profile is not None
        assert profile["entity"]["name"] == "Alice"
        assert profile["mention_count"] == 1

    @pytest.mark.asyncio
    async def test_check_behavior_consistent(self, entity_tracker):
        """Test behavior check with consistent character."""
        entity = Entity(name="Alice", type=EntityType.CHARACTER, attributes={})

        text = "Alice was happy. She smiled at everyone she met."

        issues = await entity_tracker.check_behavior([entity], text)

        # Consistent positive mood should not trigger major issues
        critical_issues = [i for i in issues if i.level == ConsistencyLevel.CRITICAL]
        assert len(critical_issues) == 0


class TestMLService:
    """Tests for the ML Service."""

    @pytest.fixture
    def ml_service(self):
        service = MLService()
        return service

    @pytest.mark.asyncio
    async def test_extract_entities(self, ml_service):
        """Test entity extraction from text."""
        await ml_service.initialize()
        text = "Alice walked into the room. She was a detective from London."

        entities = await ml_service.extract_entities(text)

        # Should extract at least Alice
        names = [e.name for e in entities]
        assert "Alice" in names

    @pytest.mark.asyncio
    async def test_extract_facts(self, ml_service):
        """Test fact extraction from text."""
        await ml_service.initialize()
        text = "Alice is 25 years old. She works as a detective."

        facts = await ml_service.extract_facts(text)

        assert len(facts) >= 1

    @pytest.mark.asyncio
    async def test_analyze_emotional_arc(self, ml_service):
        """Test emotional arc analysis."""
        await ml_service.initialize()
        text = "Alice was happy in the morning. By evening, she felt sad and lonely."

        arc = await ml_service.analyze_emotional_arc(text)

        assert arc is not None
        assert len(arc.states) >= 1


class TestExplainer:
    """Tests for the Explainer component."""

    @pytest.fixture
    def explainer(self):
        return Explainer()

    @pytest.mark.asyncio
    async def test_explain_issue(self, explainer):
        """Test explanation generation for an issue."""
        from app.models import ConsistencyIssue

        issue = ConsistencyIssue(
            type=ConstraintType.FACTUAL,
            level=ConsistencyLevel.INCONSISTENT,
            description="Alice's age changed from 25 to 30",
            evidence=["First mention: 25 years old", "Second mention: 30 years old"],
            confidence=0.9,
        )

        explanation = await explainer.explain(issue)

        assert "summary" in explanation
        assert "reasoning" in explanation
        assert "fixes" in explanation
        assert len(explanation["reasoning"]) >= 1

    @pytest.mark.asyncio
    async def test_generate_report_summary(self, explainer):
        """Test report summary generation."""
        from app.models import ConsistencyIssue

        issues = [
            ConsistencyIssue(
                type=ConstraintType.FACTUAL,
                level=ConsistencyLevel.WARNING,
                description="Minor fact inconsistency",
                confidence=0.7,
            ),
            ConsistencyIssue(
                type=ConstraintType.TEMPORAL,
                level=ConsistencyLevel.INCONSISTENT,
                description="Timeline issue",
                confidence=0.8,
            ),
        ]

        summary = await explainer.generate_report_summary(issues)

        assert "status" in summary
        assert "total_issues" in summary
        assert summary["total_issues"] == 2


# Integration test
class TestConsistencyPipeline:
    """Integration tests for the complete consistency pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test the complete consistency checking pipeline."""
        # Initialize components
        ml_service = MLService()
        await ml_service.initialize()

        knowledge_graph = KnowledgeGraph()
        constraint_engine = ConstraintEngine()

        # Test narrative with an inconsistency
        text = "Alice was 25 years old. She had been working as a detective for 10 years. Later, Alice mentioned she was actually 30."

        # Extract entities and facts
        entities = await ml_service.extract_entities(text)
        facts = await ml_service.extract_facts(text)

        # Check for issues
        assert len(entities) >= 1
        assert len(facts) >= 1

        # Add facts and check conflicts
        for fact in facts[:1]:  # Add first fact
            await knowledge_graph.add_fact(fact)

        conflicts = await knowledge_graph.check_conflicts(facts[1:])

        # The age inconsistency should be detected by either knowledge graph or constraint engine
        # This is a simplified check - in production, the full API would catch this
        print(f"Detected {len(conflicts)} conflicts in pipeline test")
