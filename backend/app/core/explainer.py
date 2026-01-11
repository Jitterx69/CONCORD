"""
Explainer - Core CONCORD Component

Provides human-understandable reasoning for all consistency decisions.
Generates explanations, evidence chains, and fix suggestions.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from app.models import (
    ConsistencyIssue,
    ConsistencyLevel,
    ConstraintType,
    Fact,
)


class Explainer:
    """
    Explainable AI module for CONCORD.

    Provides:
    - Decision reasoning chains
    - Evidence presentation
    - Confidence scoring
    - Fix suggestions
    """

    # Templates for generating explanations
    ISSUE_TEMPLATES = {
        ConstraintType.FACTUAL: {
            "prefix": "Factual Inconsistency Detected",
            "explanation": "The narrative contains contradictory facts about {subject}.",
            "impact": "This may confuse readers and break immersion.",
        },
        ConstraintType.TEMPORAL: {
            "prefix": "Timeline Issue Detected",
            "explanation": "Events in the narrative don't follow a consistent timeline.",
            "impact": "This creates logical impossibilities in the story sequence.",
        },
        ConstraintType.CAUSAL: {
            "prefix": "Causality Violation Detected",
            "explanation": "An effect is described before its cause, or a cause-effect relationship is broken.",
            "impact": "This undermines the logical flow of the narrative.",
        },
        ConstraintType.SPATIAL: {
            "prefix": "Spatial Inconsistency Detected",
            "explanation": "Characters or objects appear in impossible locations.",
            "impact": "This breaks the reader's sense of story geography.",
        },
        ConstraintType.BEHAVIORAL: {
            "prefix": "Character Behavior Issue Detected",
            "explanation": "A character is acting inconsistently with their established traits.",
            "impact": "This may feel 'out of character' to readers.",
        },
        ConstraintType.RELATIONAL: {
            "prefix": "Relationship Inconsistency Detected",
            "explanation": "Relationships between entities are contradictory.",
            "impact": "This creates confusion about character dynamics.",
        },
    }

    # Fix suggestion templates
    FIX_TEMPLATES = {
        ConstraintType.FACTUAL: [
            "Remove or modify the contradicting statement",
            "Establish that the change was intentional (e.g., character lying, time passing)",
            "Add context explaining why the fact changed",
        ],
        ConstraintType.TEMPORAL: [
            "Reorder the events to follow logical time sequence",
            "Add transition phrases to clarify time jumps",
            "Use flashback framing for out-of-order events",
        ],
        ConstraintType.CAUSAL: [
            "Move the cause before the effect in the narrative",
            "Add foreshadowing for the cause",
            "Restructure the paragraph to establish causality clearly",
        ],
        ConstraintType.SPATIAL: [
            "Add travel description between locations",
            "Adjust the timeline to allow for realistic travel",
            "Clarify that the location name is used metaphorically",
        ],
        ConstraintType.BEHAVIORAL: [
            "Add character development justifying the behavior change",
            "Show the character conflicted about their action",
            "Adjust the action to be more in-character",
        ],
        ConstraintType.RELATIONAL: [
            "Clarify how the relationship evolved",
            "Add a scene showing the relationship change",
            "Correct contradictory relationship descriptions",
        ],
    }

    def __init__(self):
        self._explanations: Dict[UUID, Dict[str, Any]] = {}

    async def explain(self, issue: ConsistencyIssue) -> Dict[str, Any]:
        """
        Generate a full explanation for a consistency issue.

        Returns:
            {
                "summary": Brief one-line summary,
                "explanation": Full explanation,
                "evidence": List of evidence items,
                "reasoning": Step-by-step reasoning,
                "impact": Potential reader impact,
                "fixes": List of suggested fixes,
                "confidence": Confidence in this assessment
            }
        """
        template = self.ISSUE_TEMPLATES.get(issue.type, {})
        fixes = self.FIX_TEMPLATES.get(issue.type, [])

        # Build reasoning chain
        reasoning = await self._build_reasoning(issue)

        explanation = {
            "summary": f"{template.get('prefix', 'Issue')}: {issue.description}",
            "explanation": template.get("explanation", "").format(
                subject=(
                    issue.description.split("'")[1] if "'" in issue.description else "the narrative"
                )
            ),
            "evidence": issue.evidence,
            "reasoning": reasoning,
            "impact": template.get("impact", "This may affect narrative quality."),
            "fixes": [
                {"suggestion": fix, "type": "automatic" if i == 0 else "manual"}
                for i, fix in enumerate(fixes)
            ],
            "confidence": issue.confidence,
            "severity": self._get_severity_description(issue.level),
        }

        self._explanations[issue.id] = explanation
        return explanation

    async def _build_reasoning(self, issue: ConsistencyIssue) -> List[str]:
        """Build a step-by-step reasoning chain for the issue."""
        steps = []

        # Step 1: What was detected
        steps.append(f"1. DETECTION: Found potential {issue.type.value} issue in the narrative")

        # Step 2: What evidence supports it
        if issue.evidence:
            steps.append(
                f"2. EVIDENCE: {len(issue.evidence)} piece(s) of supporting evidence found"
            )
            for i, evidence in enumerate(issue.evidence[:3]):  # Limit to 3
                steps.append(f"   2.{i+1}. {evidence[:100]}...")

        # Step 3: Why it's a problem
        steps.append(f"3. ANALYSIS: This creates a {issue.level.value} level inconsistency")

        # Step 4: Confidence assessment
        if issue.confidence >= 0.9:
            conf_desc = "very high confidence - clear violation detected"
        elif issue.confidence >= 0.7:
            conf_desc = "high confidence - likely a real issue"
        elif issue.confidence >= 0.5:
            conf_desc = "moderate confidence - may need human review"
        else:
            conf_desc = "low confidence - possible false positive"
        steps.append(f"4. CONFIDENCE: {conf_desc} ({issue.confidence:.0%})")

        return steps

    def _get_severity_description(self, level: ConsistencyLevel) -> Dict[str, Any]:
        """Get description for severity level."""
        descriptions = {
            ConsistencyLevel.CONSISTENT: {
                "label": "No Issue",
                "color": "green",
                "action": "No action needed",
            },
            ConsistencyLevel.WARNING: {
                "label": "Minor Issue",
                "color": "yellow",
                "action": "Consider reviewing",
            },
            ConsistencyLevel.INCONSISTENT: {
                "label": "Significant Issue",
                "color": "orange",
                "action": "Should be addressed",
            },
            ConsistencyLevel.CRITICAL: {
                "label": "Critical Issue",
                "color": "red",
                "action": "Must be fixed",
            },
        }
        return descriptions.get(level, descriptions[ConsistencyLevel.WARNING])

    async def suggest_fix(self, issue: ConsistencyIssue, facts: List[Fact]) -> Optional[str]:
        """
        Generate a specific fix suggestion for an issue.

        Uses the context from facts to provide a more targeted fix.
        """
        if not issue:
            return None

        # Get relevant facts
        relevant_facts = [
            f
            for f in facts
            if any(
                word.lower() in f.subject.lower() or word.lower() in f.object.lower()
                for word in issue.description.split()
                if len(word) > 3
            )
        ]

        # Build context-aware suggestion
        fix = issue.suggested_fix

        if not fix:
            templates = self.FIX_TEMPLATES.get(issue.type, [])
            if templates:
                fix = templates[0]

        if relevant_facts and fix:
            # Add specific context
            fact = relevant_facts[0]
            fix = f"{fix}. Consider the established fact: '{fact.subject} {fact.predicate} {fact.object}'"

        return fix

    async def generate_report_summary(self, issues: List[ConsistencyIssue]) -> Dict[str, Any]:
        """
        Generate a summary report for multiple issues.
        """
        if not issues:
            return {
                "status": "All Clear",
                "message": "No consistency issues detected in the narrative.",
                "total_issues": 0,
                "breakdown": {},
            }

        # Categorize issues
        breakdown: Dict[str, int] = {}
        for issue in issues:
            cat = issue.type.value
            breakdown[cat] = breakdown.get(cat, 0) + 1

        # Determine overall status
        critical_count = len([i for i in issues if i.level == ConsistencyLevel.CRITICAL])
        significant_count = len([i for i in issues if i.level == ConsistencyLevel.INCONSISTENT])

        if critical_count > 0:
            status = "Critical Issues Found"
            message = f"Found {critical_count} critical issue(s) that must be addressed."
        elif significant_count > 0:
            status = "Issues Found"
            message = f"Found {significant_count} significant issue(s) that should be reviewed."
        else:
            status = "Minor Issues Found"
            message = f"Found {len(issues)} minor issue(s) to consider."

        return {
            "status": status,
            "message": message,
            "total_issues": len(issues),
            "breakdown": breakdown,
            "by_severity": {
                "critical": critical_count,
                "significant": significant_count,
                "warning": len(issues) - critical_count - significant_count,
            },
            "top_issues": [
                {"type": i.type.value, "description": i.description[:100], "level": i.level.value}
                for i in sorted(issues, key=lambda x: x.confidence, reverse=True)[:5]
            ],
        }

    async def get_explanation(self, issue_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve a cached explanation."""
        return self._explanations.get(issue_id)

    def clear(self) -> None:
        """Clear cached explanations."""
        self._explanations.clear()
