"""
memory/social_memory.py — Lightweight in-memory Social Memory system.

Stores NPC interaction summaries with sentiment scores in a plain Python
dict, replacing the previous ChromaDB + sentence-transformers implementation.

The recall() method returns a sentiment score (-1 hostile → +1 friendly)
which the GOAP planner uses to dynamically adjust Socialize action cost.

Why no ChromaDB/sentence-transformers?
  Those packages pull in PyTorch, ONNX Runtime, Hugging Face Hub, etc. (~5 GB)
  which exceeds Vercel Lambda's 500 MB storage limit. The actual query
  patterns here are keyed lookups, not open-ended semantic search, so a
  plain dict is both faster and deployment-safe.
"""
from __future__ import annotations
import time
from typing import Dict, List, Optional


class _MemoryEntry:
    __slots__ = ("npc_a", "npc_b", "text", "sentiment", "timestamp")

    def __init__(self, npc_a: str, npc_b: str, text: str, sentiment: float):
        self.npc_a = npc_a
        self.npc_b = npc_b
        self.text = text
        self.sentiment = sentiment
        self.timestamp = time.time()


class SocialMemory:
    def __init__(self):
        # List of all stored memory entries (chronological)
        self._entries: List[_MemoryEntry] = []
        # Fast lookup: frozenset({npc_a, npc_b}) -> list of entries
        self._by_pair: Dict[frozenset, List[_MemoryEntry]] = {}

    # ------------------------------------------------------------------ #
    # Public API (same surface as the old ChromaDB version)               #
    # ------------------------------------------------------------------ #

    def store(
        self,
        npc_a: str,
        npc_b: str,
        event_text: str,
        sentiment: float,
    ) -> None:
        """
        Record an interaction between two NPCs.

        Args:
            npc_a, npc_b: NPC identifiers
            event_text:   Natural language description
            sentiment:    -1.0 (hostile) to +1.0 (friendly)
        """
        entry = _MemoryEntry(npc_a, npc_b, event_text, float(sentiment))
        self._entries.append(entry)

        key = frozenset({npc_a, npc_b})
        self._by_pair.setdefault(key, []).append(entry)

    def recall(self, npc_a: str, npc_b: str) -> float:
        """
        Return the average sentiment for all interactions between npc_a and npc_b.
        Returns 0.0 if no memories exist.
        """
        key = frozenset({npc_a, npc_b})
        entries = self._by_pair.get(key, [])
        if not entries:
            return 0.0
        return sum(e.sentiment for e in entries) / len(entries)

    def get_recent_memories(self, npc_id: str, limit: int = 5) -> list[dict]:
        """Get the most recent memories involving a given NPC."""
        matching = [
            e for e in self._entries
            if e.npc_a == npc_id or e.npc_b == npc_id
        ]
        matching.sort(key=lambda e: e.timestamp, reverse=True)
        return [
            {"text": e.text, "sentiment": e.sentiment, "timestamp": e.timestamp}
            for e in matching[:limit]
        ]

    def query_similar(self, query_text: str, n: int = 3) -> list[dict]:
        """
        Return recent memories whose text contains any word from the query.
        (Lightweight keyword fallback — no vector embeddings needed at runtime.)
        """
        words = set(query_text.lower().split())
        scored: List[tuple[float, _MemoryEntry]] = []
        for e in self._entries:
            overlap = sum(1 for w in words if w in e.text.lower())
            if overlap > 0:
                scored.append((overlap, e))
        scored.sort(key=lambda x: (-x[0], -x[1].timestamp))
        return [
            {
                "text":      e.text,
                "sentiment": e.sentiment,
                "timestamp": e.timestamp,
                "npc_a":     e.npc_a,
                "npc_b":     e.npc_b,
                "distance":  1.0 / (score + 1),   # pseudo-distance for API compat
            }
            for score, e in scored[:n]
        ]

