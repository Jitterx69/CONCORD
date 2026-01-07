"""
Trained Model Integration for CONCORD API
Loads the trained consistency model and provides prediction interface
"""

import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from app.models import (
    ConsistencyIssue,
    ConsistencyLevel,
    ConstraintType,
)


class TrainedConsistencyChecker:
    """
    Wrapper for the trained consistency model.
    Integrates with CONCORD's core engine.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or Path("/Users/jitterx/Desktop/CONCORD/models/consistency_model.pkl")
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.is_loaded = False
        
    async def load(self) -> bool:
        """Load the trained model"""
        try:
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.model = model_data['model']
                self.vectorizer = model_data['vectorizer']
                self.label_encoder = model_data['label_encoder']
                self.is_loaded = True
                
                print(f"✅ Loaded trained model: {model_data.get('model_name', 'Unknown')}")
                return True
            else:
                print(f"⚠️ Model not found at {self.model_path}")
                return False
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False
    
    def _extract_features(self, text: str, character: str = "", book: str = "") -> np.ndarray:
        """Extract features for prediction"""
        import re
        
        # Linguistic features (same as training)
        words = text.split()
        features = {
            'word_count': len(words),
            'char_count': len(text),
            'avg_word_length': np.mean([len(w) for w in words]) if words else 0,
            'sentence_count': len([s for s in re.split(r'[.!?]+', text) if s.strip()]),
        }
        features['avg_sentence_length'] = features['word_count'] / max(1, features['sentence_count'])
        
        temporal_markers = ['before', 'after', 'later', 'earlier', 'first', 'then']
        features['temporal_marker_count'] = sum(1 for w in words if w.lower() in temporal_markers)
        
        contradiction_markers = ['but', 'however', 'although', 'yet', 'though']
        features['contradiction_marker_count'] = sum(1 for w in words if w.lower() in contradiction_markers)
        
        features['pronoun_count'] = sum(1 for w in words if w.lower() in 
                                       ['he', 'she', 'him', 'her', 'his', 'they', 'their'])
        features['number_count'] = len(re.findall(r'\d+', text))
        features['proper_noun_count'] = len(re.findall(r'(?<!\. )[A-Z][a-z]+', text))
        features['has_dialogue'] = 1 if '"' in text or "'" in text else 0
        features['semicolon_count'] = text.count(';')
        
        # Book context features (placeholder for now)
        features['book_overlap_ratio'] = 0
        features['has_book_context'] = 0
        
        return np.array(list(features.values())).reshape(1, -1)
    
    async def predict(self, text: str, character: str = "", book: str = "") -> Dict[str, Any]:
        """
        Predict consistency/contradiction for a text segment.
        
        Returns:
            {
                'label': 'consistent' or 'contradict',
                'confidence': 0.0-1.0,
                'probabilities': {'consistent': 0.x, 'contradict': 0.y}
            }
        """
        if not self.is_loaded:
            await self.load()
            
        if not self.is_loaded:
            return {
                'label': 'unknown',
                'confidence': 0.0,
                'probabilities': {},
                'error': 'Model not loaded'
            }
        
        try:
            # Get TF-IDF features
            text_features = self.vectorizer.transform([text])
            
            # Get linguistic features
            extra_features = self._extract_features(text, character, book)
            
            # Combine features
            from scipy.sparse import hstack
            combined = hstack([text_features, extra_features])
            
            # Predict
            prediction = self.model.predict(combined)[0]
            probabilities = self.model.predict_proba(combined)[0]
            
            label = self.label_encoder.inverse_transform([prediction])[0]
            confidence = float(np.max(probabilities))
            
            prob_dict = {
                cls: float(prob) 
                for cls, prob in zip(self.label_encoder.classes_, probabilities)
            }
            
            return {
                'label': label,
                'confidence': confidence,
                'probabilities': prob_dict
            }
            
        except Exception as e:
            return {
                'label': 'error',
                'confidence': 0.0,
                'probabilities': {},
                'error': str(e)
            }
    
    async def check_narrative(self, segments: List[str]) -> List[ConsistencyIssue]:
        """
        Check multiple narrative segments for consistency issues.
        
        Returns list of ConsistencyIssue objects for segments
        predicted as contradictions.
        """
        issues = []
        
        for i, segment in enumerate(segments):
            result = await self.predict(segment)
            
            if result['label'] == 'contradict':
                issue = ConsistencyIssue(
                    type=ConstraintType.FACTUAL,
                    level=ConsistencyLevel.INCONSISTENT if result['confidence'] > 0.7 else ConsistencyLevel.WARNING,
                    description=f"Potential narrative inconsistency detected in segment {i+1}",
                    position=i,
                    evidence=[segment[:100] + "..."] if len(segment) > 100 else [segment],
                    suggested_fix="Review this segment for factual consistency with the established narrative",
                    confidence=result['confidence']
                )
                issues.append(issue)
                
        return issues


# Singleton instance
_checker = None

async def get_trained_checker() -> TrainedConsistencyChecker:
    """Get or create the trained checker singleton"""
    global _checker
    if _checker is None:
        _checker = TrainedConsistencyChecker()
        await _checker.load()
    return _checker
