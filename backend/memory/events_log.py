"""
memory/events_log.py — Append-only interaction log.

All NPC social events are written here before being fed into the
SocialMemory vector store.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class InteractionEntry:
    tick: int
    npc_a: str
    npc_b: str
    event_type: str   # "share" | "refuse" | "greet" | "argue"
    description: str
    sentiment: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "tick":        self.tick,
            "npc_a":       self.npc_a,
            "npc_b":       self.npc_b,
            "event_type":  self.event_type,
            "description": self.description,
            "sentiment":   self.sentiment,
        }


class EventsLog:
    def __init__(self, max_size: int = 200):
        self._log: List[InteractionEntry] = []
        self._max_size = max_size

    def record(
        self,
        tick: int,
        npc_a: str,
        npc_b: str,
        event_type: str,
        description: str,
        sentiment: float,
    ) -> InteractionEntry:
        entry = InteractionEntry(
            tick=tick,
            npc_a=npc_a,
            npc_b=npc_b,
            event_type=event_type,
            description=description,
            sentiment=sentiment,
        )
        self._log.append(entry)
        if len(self._log) > self._max_size:
            self._log.pop(0)
        return entry

    def recent(self, n: int = 10) -> List[InteractionEntry]:
        return list(reversed(self._log[-n:]))

    def all_entries(self) -> List[InteractionEntry]:
        return list(self._log)
