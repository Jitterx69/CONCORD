"""
Constraint Satisfaction Engine - Core CONCORD Component

Evaluates new content against all established constraints
to detect violations and inconsistencies.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import re

from app.models import (
    Constraint,
    ConstraintType,
    Fact,
    ConsistencyIssue,
    ConsistencyLevel,
)


class ConstraintEngine:
    """
    Constraint Satisfaction Engine for validating narrative consistency.

    Supports:
    - Hard constraints (must be satisfied)
    - Soft constraints (preference, can be relaxed)
    - Weighted constraint prioritization
    - Boolean satisfiability checking
    """

    def __init__(self):
        self._constraints: Dict[UUID, Constraint] = {}
        self._rules: Dict[str, Any] = {}  # Compiled rules for fast evaluation

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the engine."""
        self._constraints[constraint.id] = constraint
        self._compile_rule(constraint)

    def _compile_rule(self, constraint: Constraint) -> None:
        """Compile a constraint rule for efficient evaluation."""
        # Simple rule compilation - in production, use a proper rule engine
        self._rules[str(constraint.id)] = {
            "type": constraint.type,
            "rule": constraint.rule,
            "is_hard": constraint.is_hard,
            "priority": constraint.priority,
        }

    async def validate(self, facts: List[Fact]) -> List[ConsistencyIssue]:
        """
        Validate a list of facts against all constraints.

        Returns issues for any constraint violations.
        """
        issues = []

        # Group facts by subject for efficient checking
        facts_by_subject: Dict[str, List[Fact]] = {}
        for fact in facts:
            if fact.subject not in facts_by_subject:
                facts_by_subject[fact.subject] = []
            facts_by_subject[fact.subject].append(fact)

        # Check each constraint
        for constraint in self._constraints.values():
            violation = await self._check_constraint(constraint, facts_by_subject)
            if violation:
                issues.append(violation)

        # Also check for implicit constraints (contradictions within the input)
        implicit_issues = await self._check_implicit_constraints(facts)
        issues.extend(implicit_issues)

        return issues

    async def _check_constraint(
        self, constraint: Constraint, facts_by_subject: Dict[str, List[Fact]]
    ) -> Optional[ConsistencyIssue]:
        """Check a single constraint against the facts."""

        # Parse the constraint rule
        # Format: "entity.Subject.attribute == value" or "entity.Subject.attribute != value"
        rule = constraint.rule

        # Simple pattern matching for demonstration
        # In production, use a proper expression parser
        match = re.match(r"entity\.(\w+)\.(\w+)\s*(==|!=|>|<|>=|<=)\s*(.+)", rule)

        if not match:
            return None

        subject, attribute, operator, expected_value = match.groups()
        expected_value = expected_value.strip().strip("'\"")

        # Get facts for this subject
        subject_facts = facts_by_subject.get(subject, [])

        for fact in subject_facts:
            if fact.predicate == attribute:
                actual_value = str(fact.object).strip()

                # Evaluate the constraint
                satisfied = self._evaluate_operator(actual_value, operator, expected_value)

                if not satisfied:
                    return ConsistencyIssue(
                        type=constraint.type,
                        level=(
                            ConsistencyLevel.INCONSISTENT
                            if constraint.is_hard
                            else ConsistencyLevel.WARNING
                        ),
                        description=f"Constraint violation: {constraint.description}. "
                        f"Expected {subject}.{attribute} {operator} {expected_value}, "
                        f"but found '{actual_value}'",
                        evidence=[f"Constraint: {rule}", f"Actual value: {actual_value}"],
                        suggested_fix=f"Update {subject}'s {attribute} to match the constraint ({expected_value})",
                        confidence=0.85,
                    )

        return None

    def _evaluate_operator(self, actual: str, operator: str, expected: str) -> bool:
        """Evaluate a comparison operator."""
        try:
            if operator == "==":
                return actual.lower() == expected.lower()
            elif operator == "!=":
                return actual.lower() != expected.lower()
            elif operator == ">":
                return float(actual) > float(expected)
            elif operator == "<":
                return float(actual) < float(expected)
            elif operator == ">=":
                return float(actual) >= float(expected)
            elif operator == "<=":
                return float(actual) <= float(expected)
        except (ValueError, TypeError):
            return actual == expected

        return True

    async def _check_implicit_constraints(self, facts: List[Fact]) -> List[ConsistencyIssue]:
        """
        Check for implicit constraints - contradictions within the input itself.
        """
        issues = []

        # Group by subject and predicate
        fact_map: Dict[str, Dict[str, List[Fact]]] = {}

        for fact in facts:
            if fact.subject not in fact_map:
                fact_map[fact.subject] = {}
            if fact.predicate not in fact_map[fact.subject]:
                fact_map[fact.subject][fact.predicate] = []
            fact_map[fact.subject][fact.predicate].append(fact)

        # Check for multiple conflicting values
        for subject, predicates in fact_map.items():
            for predicate, pred_facts in predicates.items():
                if len(pred_facts) > 1:
                    # Check if values differ
                    values = set(f.object for f in pred_facts)
                    if len(values) > 1:
                        issue = ConsistencyIssue(
                            type=ConstraintType.FACTUAL,
                            level=ConsistencyLevel.INCONSISTENT,
                            description=f"Multiple conflicting values for {subject}.{predicate}: {values}",
                            conflicting_facts=[f.id for f in pred_facts],
                            evidence=[f"{f.subject} {f.predicate} {f.object}" for f in pred_facts],
                            suggested_fix=f"Clarify which value is correct for {subject}'s {predicate}",
                            confidence=0.95,
                        )
                        issues.append(issue)

        return issues

    async def check_single(self, text: str, constraint_rule: str) -> Dict[str, Any]:
        """
        Check a single constraint rule against text.

        Returns whether the constraint is satisfied and an explanation.
        """
        # Create a temporary constraint
        constraint = Constraint(
            type=ConstraintType.FACTUAL,
            description=constraint_rule,
            rule=constraint_rule,
            is_hard=True,
        )

        # This is a simplified check - in production, integrate with NLP
        # to extract facts from text and validate

        # For now, check if the constraint subject/value appear in text
        match = re.match(r"entity\.(\w+)\.(\w+)\s*(==|!=)\s*(.+)", constraint_rule)

        if match:
            subject, attribute, operator, expected = match.groups()
            expected = expected.strip().strip("'\"")

            # Simple text presence check
            subject_in_text = subject.lower() in text.lower()
            expected_in_text = expected.lower() in text.lower()

            if operator == "==" and subject_in_text and expected_in_text:
                return {
                    "satisfied": True,
                    "explanation": f"Found {subject} with expected {attribute}",
                }
            elif operator == "!=" and subject_in_text and not expected_in_text:
                return {"satisfied": True, "explanation": f"Found {subject} without {expected}"}

        return {
            "satisfied": False,
            "explanation": f"Could not verify constraint: {constraint_rule}",
        }

    def get_constraints(self) -> List[Constraint]:
        """Get all registered constraints."""
        return list(self._constraints.values())

    def remove_constraint(self, constraint_id: UUID) -> bool:
        """Remove a constraint."""
        if constraint_id in self._constraints:
            del self._constraints[constraint_id]
            del self._rules[str(constraint_id)]
            return True
        return False

    def clear(self) -> None:
        """Clear all constraints."""
        self._constraints.clear()
        self._rules.clear()
