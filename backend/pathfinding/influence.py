"""
pathfinding/influence.py — Influence Map system.

Tracks spatial danger/interest across the 30×30 grid.
- Danger sources (events, hazards) stamp Gaussian gradients.
- Values decay every tick so old threats fade out.
- A* reads influence values when computing movement costs.
"""
from __future__ import annotations
import math
from typing import List, Tuple

from world_state import GRID_W, GRID_H


class InfluenceMap:
    def __init__(self):
        self.values: List[float] = [0.0] * (GRID_W * GRID_H)

    def _idx(self, x: int, y: int) -> int:
        return y * GRID_W + x

    def add_source(
        self,
        cx: float,
        cy: float,
        strength: float = 1.0,
        radius: float = 5.0,
    ) -> None:
        """
        Stamp a Gaussian danger gradient centred at (cx, cy).
        strength: peak influence value (typically 0..1)
        radius:   effective range in tiles (sigma ≈ radius/2)
        """
        sigma = radius / 2.0
        for y in range(GRID_H):
            for x in range(GRID_W):
                dist_sq = (x - cx) ** 2 + (y - cy) ** 2
                influence = strength * math.exp(-dist_sq / (2 * sigma ** 2))
                i = self._idx(x, y)
                self.values[i] = min(1.0, self.values[i] + influence)

    def decay(self, factor: float = 0.92) -> None:
        """Reduce all influence values by decay factor each tick."""
        self.values = [v * factor for v in self.values]

    def clear(self) -> None:
        self.values = [0.0] * (GRID_W * GRID_H)

    def get(self, x: int, y: int) -> float:
        return self.values[self._idx(x, y)]

    def as_list(self) -> List[float]:
        return list(self.values)

    def apply_events(self, events: list) -> None:
        """Stamp influence sources for all active game events."""
        for event in events:
            if event.position is not None:
                ex, ey = event.position
                self.add_source(ex, ey, strength=0.95, radius=6.0)
