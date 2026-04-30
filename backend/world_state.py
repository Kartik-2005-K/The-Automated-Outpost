"""
world_state.py — Central data models for the Automated Outpost simulation.
All mutable state lives here; the tick loop mutates it and broadcasts it.
"""
from __future__ import annotations
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ──────────────────────────────────────────────
# Grid constants
# ──────────────────────────────────────────────
GRID_W = 30
GRID_H = 30

# ──────────────────────────────────────────────
# Resource types
# ──────────────────────────────────────────────
RESOURCE_FOOD  = "Food"
RESOURCE_FUEL  = "Fuel"
RESOURCE_SCRAP = "Scrap"

# ──────────────────────────────────────────────
# NPC Stats
# ──────────────────────────────────────────────
STAT_MAX = 100.0

@dataclass
class Stats:
    energy: float = 100.0
    hunger: float = 100.0   # high = full, low = starving
    social: float = 80.0

    def decay(self, tick: int):
        """Called each tick; stats degrade over time."""
        self.energy = max(0.0, self.energy - 0.8)
        self.hunger = max(0.0, self.hunger - 1.2)
        self.social = max(0.0, self.social - 0.5)

    def to_dict(self):
        return {"energy": round(self.energy, 1),
                "hunger": round(self.hunger, 1),
                "social": round(self.social, 1)}


# ──────────────────────────────────────────────
# NPC
# ──────────────────────────────────────────────
COLORS = ["#4FC3F7", "#81C784", "#FFB74D", "#CE93D8"]

@dataclass
class NPC:
    id: str
    name: str
    color: str
    position: List[float] = field(default_factory=lambda: [0.0, 0.0])
    stats: Stats = field(default_factory=Stats)

    # Inventory flags (simplified — bool per item)
    has_food: bool   = False
    has_fuel: bool   = False
    has_scrap: bool  = False
    food_cooked: bool = False

    # AI state
    current_goal: str     = "Idle"
    current_plan: List[str] = field(default_factory=list)
    current_action: str   = "Idle"
    action_progress: float = 0.0   # 0..1 within current action

    # Pathfinding
    target_position: Optional[List[float]] = None
    path: List[List[float]] = field(default_factory=list)

    # Social
    social_scores: Dict[str, float] = field(default_factory=dict)  # peer_id → score

    # Status text for debug overlay
    status: str = "Initializing..."

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "position": self.position,
            "stats": self.stats.to_dict(),
            "has_food": self.has_food,
            "has_fuel": self.has_fuel,
            "has_scrap": self.has_scrap,
            "food_cooked": self.food_cooked,
            "current_goal": self.current_goal,
            "current_plan": self.current_plan,
            "current_action": self.current_action,
            "action_progress": round(self.action_progress, 2),
            "path": self.path,
            "social_scores": self.social_scores,
            "status": self.status,
        }


# ──────────────────────────────────────────────
# Resource Node
# ──────────────────────────────────────────────
@dataclass
class Resource:
    id: str
    type: str
    position: List[float]
    quantity: int = 5

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "quantity": self.quantity,
        }


# ──────────────────────────────────────────────
# Active Event
# ──────────────────────────────────────────────
@dataclass
class GameEvent:
    id: str
    name: str
    description: str
    position: Optional[List[float]]   # map coords of danger source (if any)
    duration_ticks: int
    remaining_ticks: int
    danger_strength: float = 60.0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "position": self.position,
            "remaining_ticks": self.remaining_ticks,
            "duration_ticks": self.duration_ticks,
        }


# ──────────────────────────────────────────────
# World State (singleton mutated by tick loop)
# ──────────────────────────────────────────────
@dataclass
class WorldState:
    tick: int = 0
    base_integrity: float = 100.0

    npcs: List[NPC] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    events: List[GameEvent] = field(default_factory=list)

    # 30×30 flat arrays (row-major)
    grid: List[int] = field(default_factory=lambda: [1] * (GRID_W * GRID_H))
    influence_map: List[float] = field(default_factory=lambda: [0.0] * (GRID_W * GRID_H))

    def to_dict(self):
        return {
            "tick": self.tick,
            "base_integrity": round(self.base_integrity, 1),
            "npcs": [n.to_dict() for n in self.npcs],
            "resources": [r.to_dict() for r in self.resources],
            "events": [e.to_dict() for e in self.events],
            "grid": self.grid,
            "influence_map": [round(v, 2) for v in self.influence_map],
        }


# ──────────────────────────────────────────────
# World Factory — initial layout
# ──────────────────────────────────────────────
def build_initial_world() -> WorldState:
    ws = WorldState()

    # ── Static obstacles (ring of walls + some rocks) ──
    for x in range(GRID_W):
        ws.grid[0 * GRID_W + x] = 0          # top wall
        ws.grid[(GRID_H-1) * GRID_W + x] = 0 # bottom wall
    for y in range(GRID_H):
        ws.grid[y * GRID_W + 0] = 0          # left wall
        ws.grid[y * GRID_W + (GRID_W-1)] = 0 # right wall

    # Interior rocks
    rock_positions = [
        (5,5),(5,6),(6,5),
        (10,12),(11,12),(12,12),(12,13),
        (20,8),(20,9),(21,8),
        (15,20),(16,20),(15,21),
        (8,22),(9,22),(8,23),
        (24,18),(24,19),(25,18),
    ]
    for (rx, ry) in rock_positions:
        ws.grid[ry * GRID_W + rx] = 0

    # ── NPCs ──
    npc_starts = [[3, 3], [3, 26], [26, 3], [26, 26]]
    npc_names  = ["ARIA", "BOLT", "CODA", "DUSK"]
    for i in range(4):
        npc = NPC(
            id=f"npc_{i}",
            name=npc_names[i],
            color=COLORS[i],
            position=list(npc_starts[i]),
            stats=Stats(
                energy=random.uniform(60, 100),
                hunger=random.uniform(50, 100),
                social=random.uniform(40, 80),
            )
        )
        ws.npcs.append(npc)

    # ── Resources scattered across map ──
    resource_data = [
        (RESOURCE_FOOD,  [14, 5]),
        (RESOURCE_FOOD,  [7,  17]),
        (RESOURCE_FOOD,  [22, 14]),
        (RESOURCE_FUEL,  [18, 6]),
        (RESOURCE_FUEL,  [5,  14]),
        (RESOURCE_FUEL,  [24, 22]),
        (RESOURCE_SCRAP, [12, 25]),
        (RESOURCE_SCRAP, [20, 20]),
        (RESOURCE_SCRAP, [8,  8]),
    ]
    for i, (rtype, rpos) in enumerate(resource_data):
        ws.resources.append(Resource(
            id=f"res_{i}",
            type=rtype,
            position=rpos,
            quantity=random.randint(3, 8),
        ))

    return ws
