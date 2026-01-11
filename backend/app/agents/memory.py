from typing import List, Dict, Any
from uuid import UUID
import numpy as np
from sentence_transformers import SentenceTransformer


class AgentMemory:
    """
    Episodic memory for BDI agents.
    Stores 'memories' as text + embedding.
    Allows recall based on semantic similarity.
    """

    def __init__(self):
        # In production, use a proper Vector DB (Chroma, Pinecone, etc.)
        # For PoC, usage in-memory persistence
        self.memories: List[Dict[str, Any]] = []
        # Lazy load encoder on first use or init
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        # Try to load C Vector Store
        self.c_store = None
        try:
            import ctypes
            import os
            import sys

            lib_name = "libvector.so" if sys.platform != "darwin" else "libvector.dylib"
            lib_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../c_vector", lib_name)
            )

            self.vec_lib = ctypes.CDLL(lib_path)
            # Define signatures...
            print("🚀 C Vector Store: Optimization Library Loaded")
        except Exception as e:
            print(f"⚠️ Could not load C Vector Store: {e}")

    def remember(self, entity_id: UUID, text: str, importance: float = 1.0) -> None:
        """Store a new memory"""
        embedding = self.encoder.encode(text)
        self.memories.append(
            {
                "entity_id": entity_id,
                "text": text,
                "embedding": embedding,
                "importance": importance,
            }
        )

    def recall(self, entity_id: UUID, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant memories for this agent context"""
        if not self.memories:
            return []

        # Filter by agent
        agent_memories = [m for m in self.memories if m["entity_id"] == entity_id]
        if not agent_memories:
            return []

        q_vec = self.encoder.encode(query)

        # Calculate scores
        results = []
        for mem in agent_memories:
            # Cosine similarity
            score = np.dot(mem["embedding"], q_vec) / (
                np.linalg.norm(mem["embedding"]) * np.linalg.norm(q_vec) + 1e-9
            )
            # Weight by importance
            weighted_score = score * mem["importance"]
            results.append((weighted_score, mem["text"]))

        # Sort and return top_k
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]
