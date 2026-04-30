"""
memory/social_memory.py — RAG-based Social Memory system.

Uses ChromaDB (in-memory) + sentence-transformers to store and retrieve
NPC interaction summaries as vector embeddings.

The recall() method returns a sentiment score (-1 hostile → +1 friendly)
which the GOAP planner uses to dynamically adjust Socialize action cost.
"""
from __future__ import annotations
import time
from typing import Optional
import chromadb
from sentence_transformers import SentenceTransformer


EMBED_MODEL = "all-MiniLM-L6-v2"   # ~80MB, downloads once


class SocialMemory:
    def __init__(self):
        self._client = chromadb.EphemeralClient()
        self._collection = self._client.get_or_create_collection(
            name="npc_interactions",
            metadata={"hnsw:space": "cosine"},
        )
        self._model: Optional[SentenceTransformer] = None
        self._memory_count = 0

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(EMBED_MODEL)
        return self._model

    def store(
        self,
        npc_a: str,
        npc_b: str,
        event_text: str,
        sentiment: float,   # -1.0 hostile → +1.0 friendly
    ) -> None:
        """
        Embed an interaction summary and store it in the vector DB.
        
        Args:
            npc_a, npc_b: NPC identifiers
            event_text:   Natural language description, e.g. "ARIA shared food with BOLT"
            sentiment:    -1.0 to +1.0
        """
        model = self._get_model()
        embedding = model.encode(event_text).tolist()
        self._memory_count += 1
        doc_id = f"mem_{npc_a}_{npc_b}_{self._memory_count}"

        self._collection.add(
            documents=[event_text],
            embeddings=[embedding],
            ids=[doc_id],
            metadatas=[{
                "npc_a":     npc_a,
                "npc_b":     npc_b,
                "sentiment": float(sentiment),
                "timestamp": time.time(),
            }],
        )

    def recall(self, npc_a: str, npc_b: str) -> float:
        """
        Retrieve the average sentiment score for interactions between npc_a and npc_b.
        Returns 0.0 if no memories exist.
        """
        try:
            results = self._collection.get(
                where={"$and": [
                    {"npc_a": {"$in": [npc_a, npc_b]}},
                    {"npc_b": {"$in": [npc_a, npc_b]}},
                ]},
                include=["metadatas"],
            )
            metas = results.get("metadatas", [])
            if not metas:
                return 0.0
            scores = [m["sentiment"] for m in metas]
            return sum(scores) / len(scores)
        except Exception:
            return 0.0

    def get_recent_memories(self, npc_id: str, limit: int = 5) -> list[dict]:
        """Get most recent memories involving an NPC."""
        try:
            results = self._collection.get(
                where={"$or": [
                    {"npc_a": {"$eq": npc_id}},
                    {"npc_b": {"$eq": npc_id}},
                ]},
                include=["documents", "metadatas"],
            )
            docs = results.get("documents", [])
            metas = results.get("metadatas", [])
            combined = [
                {"text": d, "sentiment": m.get("sentiment", 0), "timestamp": m.get("timestamp", 0)}
                for d, m in zip(docs, metas)
            ]
            combined.sort(key=lambda x: x["timestamp"], reverse=True)
            return combined[:limit]
        except Exception:
            return []

    def query_similar(self, query_text: str, n: int = 3) -> list[dict]:
        """Semantic search over all stored memories."""
        try:
            model = self._get_model()
            q_vec = model.encode(query_text).tolist()
            results = self._collection.query(
                query_embeddings=[q_vec],
                n_results=min(n, self._memory_count or 1),
                include=["documents", "metadatas", "distances"],
            )
            out = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                out.append({"text": doc, "distance": dist, **meta})
            return out
        except Exception:
            return []
