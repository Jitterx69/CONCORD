"""
Consistency check endpoints - Core CONCORD functionality
"""

from fastapi import APIRouter, Request, HTTPException
from typing import List, Optional
from uuid import UUID
import time

from app.models import (
    ConsistencyCheckRequest,
    ConsistencyCheckResponse,
    ConsistencyReport,
    ConsistencyIssue,
    ConsistencyLevel,
    ConstraintType,
    EmotionalArc,
    Fact,
)

router = APIRouter()


@router.post("/check", response_model=ConsistencyCheckResponse)
async def check_consistency(request: ConsistencyCheckRequest, req: Request):
    """
    Check narrative text for consistency issues.

    This is the main CONCORD endpoint that:
    1. Extracts entities and facts from the text
    2. Validates against existing knowledge graph
    3. Checks temporal, causal, and relational consistency
    4. Analyzes emotional arc (optional)
    5. Suggests fixes for inconsistencies (optional)
    """
    start_time = time.time()

    # Get services from app state
    knowledge_graph = req.app.state.knowledge_graph
    constraint_engine = req.app.state.constraint_engine
    temporal_reasoner = req.app.state.temporal_reasoner
    entity_tracker = req.app.state.entity_tracker
    explainer = req.app.state.explainer
    ml_service = req.app.state.ml_service

    # Step 1: Extract entities and facts from input text
    extracted_facts = await ml_service.extract_facts(request.text)
    entities = await ml_service.extract_entities(request.text)

    # Step 2: Add any pre-existing facts
    all_facts = extracted_facts
    if request.existing_facts:
        all_facts.extend(request.existing_facts)

    # Step 3: Check for conflicts in knowledge graph
    issues: List[ConsistencyIssue] = []

    # Factual consistency
    factual_issues = await knowledge_graph.check_conflicts(extracted_facts)
    issues.extend(factual_issues)

    # Temporal consistency
    if request.check_temporal:
        temporal_issues = await temporal_reasoner.check_timeline(request.text, all_facts)
        issues.extend(temporal_issues)

    # Entity behavioral consistency
    behavioral_issues = await entity_tracker.check_behavior(entities, request.text)
    issues.extend(behavioral_issues)

    # Constraint validation
    constraint_issues = await constraint_engine.validate(all_facts)
    issues.extend(constraint_issues)

    # Step 4: Emotional analysis
    emotional_arc = None
    if request.check_emotional:
        emotional_arc = await ml_service.analyze_emotional_arc(request.text)

    # Step 5: Generate fixes if requested
    suggested_fixes = []
    if request.auto_fix and issues:
        for issue in issues:
            fix = await explainer.suggest_fix(issue, all_facts)
            if fix:
                suggested_fixes.append(fix)
                issue.suggested_fix = fix

    # Calculate scores
    total_checks = len(all_facts) + len(entities)
    issue_count = len(issues)
    overall_score = max(0.0, 1.0 - (issue_count * 0.1)) if total_checks > 0 else 1.0

    # Determine overall level
    if overall_score >= 0.9:
        level = ConsistencyLevel.CONSISTENT
    elif overall_score >= 0.7:
        level = ConsistencyLevel.WARNING
    elif overall_score >= 0.4:
        level = ConsistencyLevel.INCONSISTENT
    else:
        level = ConsistencyLevel.CRITICAL

    # Category scores
    factual_score = 1.0 - (len([i for i in issues if i.type == ConstraintType.FACTUAL]) * 0.15)
    temporal_score = 1.0 - (len([i for i in issues if i.type == ConstraintType.TEMPORAL]) * 0.15)
    causal_score = 1.0 - (len([i for i in issues if i.type == ConstraintType.CAUSAL]) * 0.15)
    spatial_score = 1.0 - (len([i for i in issues if i.type == ConstraintType.SPATIAL]) * 0.15)
    behavioral_score = 1.0 - (
        len([i for i in issues if i.type == ConstraintType.BEHAVIORAL]) * 0.15
    )
    relational_score = 1.0 - (
        len([i for i in issues if i.type == ConstraintType.RELATIONAL]) * 0.15
    )

    # Build report
    from uuid import uuid4

    report = ConsistencyReport(
        id=uuid4(),
        narrative_id=uuid4(),  # Would be provided for existing narratives
        overall_score=max(0.0, min(1.0, overall_score)),
        level=level,
        issues=issues,
        facts_checked=len(all_facts),
        constraints_validated=len(constraint_issues),
        entities_tracked=len(entities),
        analysis_time_ms=(time.time() - start_time) * 1000,
        factual_score=max(0.0, factual_score),
        temporal_score=max(0.0, temporal_score),
        causal_score=max(0.0, causal_score),
        spatial_score=max(0.0, spatial_score),
        behavioral_score=max(0.0, behavioral_score),
        relational_score=max(0.0, relational_score),
    )

    return ConsistencyCheckResponse(
        report=report,
        emotional_arc=emotional_arc,
        suggested_fixes=suggested_fixes,
        processing_time_ms=(time.time() - start_time) * 1000,
    )


@router.post("/validate")
async def validate_against_constraints(text: str, constraints: List[str], req: Request):
    """
    Validate text against a specific set of constraints.

    Useful for checking if new content violates known rules.
    """
    constraint_engine = req.app.state.constraint_engine

    issues = []
    for constraint in constraints:
        result = await constraint_engine.check_single(text, constraint)
        if not result["satisfied"]:
            issues.append(
                {
                    "constraint": constraint,
                    "violated": True,
                    "explanation": result.get("explanation", "Constraint violated"),
                }
            )

    return {
        "valid": len(issues) == 0,
        "violations": issues,
        "constraints_checked": len(constraints),
    }


@router.get("/report/{report_id}")
async def get_report(report_id: UUID):
    """
    Retrieve a previously generated consistency report.
    """
    # In production, this would fetch from database
    raise HTTPException(
        status_code=404,
        detail=f"Report {report_id} not found. Reports are currently not persisted.",
    )


@router.get("/issues/types")
async def get_issue_types():
    """
    Get all available consistency issue types.
    """
    return {
        "types": [t.value for t in ConstraintType],
        "levels": [l.value for l in ConsistencyLevel],
        "descriptions": {
            ConstraintType.FACTUAL.value: "Facts contradict established truths",
            ConstraintType.TEMPORAL.value: "Timeline or sequence inconsistencies",
            ConstraintType.CAUSAL.value: "Cause-effect logic violations",
            ConstraintType.SPATIAL.value: "Location or movement impossibilities",
            ConstraintType.BEHAVIORAL.value: "Character behavior inconsistencies",
            ConstraintType.RELATIONAL.value: "Relationship contradictions",
        },
    }
