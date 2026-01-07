"""
Self-Healing Narrative Fixer - CONCORD Super Enhancement

Automatically detects and suggests fixes for narrative inconsistencies.
Provides multiple fix options ranked by quality and minimal disruption.
"""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass
from enum import Enum
import re

from app.models import (
    ConsistencyIssue,
    ConsistencyLevel,
    ConstraintType,
    Fact,
)


class FixType(str, Enum):
    """Types of fixes that can be applied."""
    REPLACE = "replace"          # Replace text with corrected version
    INSERT = "insert"            # Insert additional text
    DELETE = "delete"            # Remove problematic text
    REORDER = "reorder"          # Change order of elements
    CLARIFY = "clarify"          # Add clarifying information
    RETCON = "retcon"            # Retroactively change established fact


@dataclass
class FixSuggestion:
    """A suggested fix for a consistency issue."""
    id: UUID
    issue_id: UUID
    fix_type: FixType
    description: str
    original_text: str
    suggested_text: str
    position: Optional[int]
    confidence: float
    impact_score: float  # How much does this change the narrative? (0=minimal, 1=major)
    auto_applicable: bool  # Can be applied automatically without review


class NarrativeFixer:
    """
    Self-healing system for automatic narrative repair.
    
    Capabilities:
    - Generate fix suggestions for detected issues
    - Rank fixes by quality and minimal disruption
    - Apply fixes automatically (Level 1) or with approval (Level 2-4)
    - Learn from approved fixes to improve suggestions
    """
    
    # Fix templates for different issue types
    FIX_TEMPLATES = {
        ConstraintType.FACTUAL: [
            {
                "pattern": r"(\w+)\s+(?:is|was)\s+(\d+)\s+years?\s+old",
                "description": "Age inconsistency fix",
                "template": "{subject} is {correct_value} years old",
            },
            {
                "pattern": r"(\w+)(?:'s)?\s+(\w+)\s+(?:is|was|were|are)\s+(\w+)",
                "description": "Attribute inconsistency fix",
                "template": "{subject}'s {attribute} is {correct_value}",
            },
        ],
        ConstraintType.TEMPORAL: [
            {
                "pattern": r"(before|after|during|while)\s+([^,\.]+)",
                "description": "Temporal marker fix",
                "template": "{correct_marker} {event}",
            },
        ],
        ConstraintType.BEHAVIORAL: [
            {
                "pattern": r"(\w+)\s+(said|shouted|whispered|muttered)\s+([^\.]+)",
                "description": "Dialogue tone fix",
                "template": "{character} {correct_verb} {dialogue}",
            },
        ],
    }
    
    # Transition phrases for smooth fixes
    TRANSITION_PHRASES = {
        "explanation": [
            "As it turned out, ",
            "Upon reflection, ",
            "In truth, ",
            "What {subject} hadn't mentioned was that ",
        ],
        "revision": [
            "Actually, ",
            "To be precise, ",
            "More accurately, ",
        ],
        "time_lapse": [
            "Some time later, ",
            "After a while, ",
            "Eventually, ",
        ],
        "mood_shift": [
            "Gradually, {character}'s mood shifted. ",
            "As the moment passed, ",
            "With a deep breath, ",
        ],
    }
    
    def __init__(self):
        self._suggestions: Dict[UUID, List[FixSuggestion]] = {}
        self._applied_fixes: List[FixSuggestion] = []
        self._fix_history: List[Dict[str, Any]] = []
        
    async def generate_fixes(
        self, 
        issue: ConsistencyIssue,
        facts: List[Fact],
        narrative_text: str
    ) -> List[FixSuggestion]:
        """
        Generate fix suggestions for a consistency issue.
        
        Returns multiple options ranked by quality.
        """
        suggestions = []
        
        # Get relevant facts for context
        relevant_facts = await self._get_relevant_facts(issue, facts)
        
        # Generate fixes based on issue type
        if issue.type == ConstraintType.FACTUAL:
            suggestions.extend(
                await self._generate_factual_fixes(issue, relevant_facts, narrative_text)
            )
        elif issue.type == ConstraintType.TEMPORAL:
            suggestions.extend(
                await self._generate_temporal_fixes(issue, narrative_text)
            )
        elif issue.type == ConstraintType.BEHAVIORAL:
            suggestions.extend(
                await self._generate_behavioral_fixes(issue, narrative_text)
            )
        elif issue.type == ConstraintType.CAUSAL:
            suggestions.extend(
                await self._generate_causal_fixes(issue, narrative_text)
            )
        elif issue.type == ConstraintType.SPATIAL:
            suggestions.extend(
                await self._generate_spatial_fixes(issue, narrative_text)
            )
        else:
            # Generic fix
            suggestions.append(await self._generate_generic_fix(issue))
            
        # Sort by confidence and impact
        suggestions.sort(key=lambda s: (s.confidence, -s.impact_score), reverse=True)
        
        # Store suggestions
        if issue.id not in self._suggestions:
            self._suggestions[issue.id] = []
        self._suggestions[issue.id].extend(suggestions)
        
        return suggestions
    
    async def _get_relevant_facts(
        self, 
        issue: ConsistencyIssue, 
        facts: List[Fact]
    ) -> List[Fact]:
        """Get facts relevant to an issue."""
        relevant = []
        
        # Extract potential subjects from issue description
        words = issue.description.split()
        potential_subjects = [w.strip("'\".,") for w in words if w[0].isupper() and len(w) > 1]
        
        for fact in facts:
            if any(subj.lower() == fact.subject.lower() for subj in potential_subjects):
                relevant.append(fact)
                
        return relevant
    
    async def _generate_factual_fixes(
        self, 
        issue: ConsistencyIssue,
        facts: List[Fact],
        text: str
    ) -> List[FixSuggestion]:
        """Generate fixes for factual inconsistencies."""
        suggestions = []
        
        # Try to identify the conflicting values
        match = re.search(r"Existing:\s*'([^']+)'.*New:\s*'([^']+)'", issue.description)
        
        if match:
            existing_value = match.group(1)
            new_value = match.group(2)
            
            # Option 1: Keep the existing value (minimal disruption)
            suggestions.append(FixSuggestion(
                id=uuid4(),
                issue_id=issue.id,
                fix_type=FixType.REPLACE,
                description=f"Keep established value '{existing_value}' (minimal change)",
                original_text=new_value,
                suggested_text=existing_value,
                position=issue.position,
                confidence=0.8,
                impact_score=0.2,
                auto_applicable=True
            ))
            
            # Option 2: Accept the new value and update history
            suggestions.append(FixSuggestion(
                id=uuid4(),
                issue_id=issue.id,
                fix_type=FixType.RETCON,
                description=f"Accept new value '{new_value}' and update narrative",
                original_text=existing_value,
                suggested_text=new_value,
                position=None,  # Needs to update earlier mention
                confidence=0.6,
                impact_score=0.6,
                auto_applicable=False
            ))
            
            # Option 3: Add explanation for the change
            explanation = f"(though it had once been {existing_value})"
            suggestions.append(FixSuggestion(
                id=uuid4(),
                issue_id=issue.id,
                fix_type=FixType.CLARIFY,
                description="Add clarifying explanation for the discrepancy",
                original_text=new_value,
                suggested_text=f"{new_value} {explanation}",
                position=issue.position,
                confidence=0.7,
                impact_score=0.4,
                auto_applicable=False
            ))
            
        return suggestions
    
    async def _generate_temporal_fixes(
        self, 
        issue: ConsistencyIssue,
        text: str
    ) -> List[FixSuggestion]:
        """Generate fixes for temporal inconsistencies."""
        suggestions = []
        
        # Option 1: Add time transition phrase
        for phrase in self.TRANSITION_PHRASES["time_lapse"]:
            suggestions.append(FixSuggestion(
                id=uuid4(),
                issue_id=issue.id,
                fix_type=FixType.INSERT,
                description=f"Add time transition: '{phrase.strip()}'",
                original_text="",
                suggested_text=phrase,
                position=issue.position,
                confidence=0.75,
                impact_score=0.2,
                auto_applicable=True
            ))
            break  # Just use first one for auto
            
        # Option 2: Reorder events (if positions are provided in evidence)
        suggestions.append(FixSuggestion(
            id=uuid4(),
            issue_id=issue.id,
            fix_type=FixType.REORDER,
            description="Reorder events to fix timeline",
            original_text="[current order]",
            suggested_text="[chronological order]",
            position=issue.position,
            confidence=0.6,
            impact_score=0.7,
            auto_applicable=False
        ))
        
        return suggestions
    
    async def _generate_behavioral_fixes(
        self, 
        issue: ConsistencyIssue,
        text: str
    ) -> List[FixSuggestion]:
        """Generate fixes for behavioral inconsistencies."""
        suggestions = []
        
        # Extract character name from issue
        name_match = re.search(r"(\w+)\s+(?:is|showing|acting)", issue.description)
        character = name_match.group(1) if name_match else "the character"
        
        # Option 1: Add mood transition
        transition = self.TRANSITION_PHRASES["mood_shift"][0].format(character=character)
        suggestions.append(FixSuggestion(
            id=uuid4(),
            issue_id=issue.id,
            fix_type=FixType.INSERT,
            description="Add emotional transition phrase",
            original_text="",
            suggested_text=transition,
            position=issue.position,
            confidence=0.8,
            impact_score=0.3,
            auto_applicable=True
        ))
        
        # Option 2: Add internal justification
        justification = f"Even {character} was surprised by the sudden change within. "
        suggestions.append(FixSuggestion(
            id=uuid4(),
            issue_id=issue.id,
            fix_type=FixType.INSERT,
            description="Add character self-awareness of mood shift",
            original_text="",
            suggested_text=justification,
            position=issue.position,
            confidence=0.7,
            impact_score=0.4,
            auto_applicable=False
        ))
        
        return suggestions
    
    async def _generate_causal_fixes(
        self, 
        issue: ConsistencyIssue,
        text: str
    ) -> List[FixSuggestion]:
        """Generate fixes for causal inconsistencies."""
        suggestions = []
        
        # Option 1: Add foreshadowing phrase
        foreshadowing = "Little did they know, what would happen next would change everything. "
        suggestions.append(FixSuggestion(
            id=uuid4(),
            issue_id=issue.id,
            fix_type=FixType.INSERT,
            description="Add foreshadowing before the effect",
            original_text="",
            suggested_text=foreshadowing,
            position=issue.position,
            confidence=0.6,
            impact_score=0.3,
            auto_applicable=False
        ))
        
        # Option 2: Add causal connector
        connector = "As a result of what came before, "
        suggestions.append(FixSuggestion(
            id=uuid4(),
            issue_id=issue.id,
            fix_type=FixType.INSERT,
            description="Add causal connector phrase",
            original_text="",
            suggested_text=connector,
            position=issue.position,
            confidence=0.7,
            impact_score=0.2,
            auto_applicable=True
        ))
        
        return suggestions
    
    async def _generate_spatial_fixes(
        self, 
        issue: ConsistencyIssue,
        text: str
    ) -> List[FixSuggestion]:
        """Generate fixes for spatial inconsistencies."""
        suggestions = []
        
        # Option 1: Add travel description
        travel = "After the long journey, "
        suggestions.append(FixSuggestion(
            id=uuid4(),
            issue_id=issue.id,
            fix_type=FixType.INSERT,
            description="Add travel transition",
            original_text="",
            suggested_text=travel,
            position=issue.position,
            confidence=0.75,
            impact_score=0.3,
            auto_applicable=True
        ))
        
        # Option 2: Add detailed travel
        detailed_travel = "The journey took several days, but finally, "
        suggestions.append(FixSuggestion(
            id=uuid4(),
            issue_id=issue.id,
            fix_type=FixType.INSERT,
            description="Add detailed travel description",
            original_text="",
            suggested_text=detailed_travel,
            position=issue.position,
            confidence=0.65,
            impact_score=0.5,
            auto_applicable=False
        ))
        
        return suggestions
    
    async def _generate_generic_fix(self, issue: ConsistencyIssue) -> FixSuggestion:
        """Generate a generic fix suggestion."""
        return FixSuggestion(
            id=uuid4(),
            issue_id=issue.id,
            fix_type=FixType.CLARIFY,
            description="Review and manually correct this issue",
            original_text="[problematic section]",
            suggested_text="[requires manual review]",
            position=issue.position,
            confidence=0.5,
            impact_score=0.5,
            auto_applicable=False
        )
    
    async def apply_fix(
        self, 
        suggestion: FixSuggestion,
        narrative_text: str
    ) -> Tuple[str, bool]:
        """
        Apply a fix suggestion to the narrative text.
        
        Returns (fixed_text, success).
        """
        try:
            if suggestion.fix_type == FixType.REPLACE:
                fixed_text = narrative_text.replace(
                    suggestion.original_text,
                    suggestion.suggested_text,
                    1  # Only replace first occurrence
                )
            elif suggestion.fix_type == FixType.INSERT:
                if suggestion.position is not None:
                    sentences = narrative_text.split('.')
                    if suggestion.position < len(sentences):
                        sentences[suggestion.position] = (
                            suggestion.suggested_text + sentences[suggestion.position]
                        )
                        fixed_text = '.'.join(sentences)
                    else:
                        fixed_text = narrative_text + " " + suggestion.suggested_text
                else:
                    fixed_text = narrative_text + " " + suggestion.suggested_text
            elif suggestion.fix_type == FixType.DELETE:
                fixed_text = narrative_text.replace(suggestion.original_text, "", 1)
            else:
                return narrative_text, False
                
            self._applied_fixes.append(suggestion)
            self._fix_history.append({
                "suggestion_id": str(suggestion.id),
                "fix_type": suggestion.fix_type.value,
                "success": True
            })
            
            return fixed_text, True
            
        except Exception as e:
            self._fix_history.append({
                "suggestion_id": str(suggestion.id),
                "fix_type": suggestion.fix_type.value,
                "success": False,
                "error": str(e)
            })
            return narrative_text, False
    
    async def get_auto_fixes(
        self, 
        issues: List[ConsistencyIssue],
        facts: List[Fact],
        narrative_text: str
    ) -> List[FixSuggestion]:
        """
        Get all auto-applicable fixes for a list of issues.
        
        Only returns Level 1 (automatic) fixes with high confidence.
        """
        auto_fixes = []
        
        for issue in issues:
            suggestions = await self.generate_fixes(issue, facts, narrative_text)
            
            for suggestion in suggestions:
                if suggestion.auto_applicable and suggestion.confidence >= 0.7:
                    auto_fixes.append(suggestion)
                    break  # Only one auto-fix per issue
                    
        return auto_fixes
    
    def get_fix_history(self) -> List[Dict[str, Any]]:
        """Get history of applied fixes."""
        return self._fix_history
    
    def clear(self) -> None:
        """Clear all suggestions and history."""
        self._suggestions.clear()
        self._applied_fixes.clear()
        self._fix_history.clear()
