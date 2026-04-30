"""
goap/actions.py — All NPC actions for the GOAP planner.

Each Action defines:
  - preconditions: dict of world-state flags that must be satisfied
  - effects: dict of world-state changes after execution
  - cost: base planning cost (lower = preferred)
  - duration_ticks: how many sim ticks the action takes to execute
  - target_type: "resource"/"npc"/None — what spatial target to move toward
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class Action:
    name: str
    preconditions: Dict[str, Any]
    effects: Dict[str, Any]
    cost: float
    duration_ticks: int = 3
    target_type: Optional[str] = None  # "food"/"fuel"/"scrap"/"npc"/"base"/None
    description: str = ""

    def is_applicable(self, state: Dict[str, Any]) -> bool:
        """Check if all preconditions are satisfied in the given world-state snapshot."""
        for key, val in self.preconditions.items():
            if isinstance(val, tuple):
                # (operator, threshold)  e.g. (">", 10)
                op, threshold = val
                actual = state.get(key, 0)
                if op == ">"  and not (actual > threshold):  return False
                if op == ">=" and not (actual >= threshold): return False
                if op == "<"  and not (actual < threshold):  return False
                if op == "<=" and not (actual <= threshold): return False
            else:
                if state.get(key) != val:
                    return False
        return True

    def apply(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new state dict with this action's effects applied."""
        new_state = dict(state)
        for key, delta in self.effects.items():
            if isinstance(delta, tuple):
                op, val = delta
                if op == "+=": new_state[key] = new_state.get(key, 0) + val
                if op == "-=": new_state[key] = new_state.get(key, 0) - val
                if op == "=":  new_state[key] = val
            else:
                new_state[key] = delta
        return new_state


# ──────────────────────────────────────────────
# Action Library
# ──────────────────────────────────────────────
def get_all_actions() -> list[Action]:
    return [
        Action(
            name="Idle",
            preconditions={},
            effects={},
            cost=1,
            duration_ticks=2,
            target_type=None,
            description="Stand by and conserve energy.",
        ),
        Action(
            name="Sleep",
            preconditions={"energy": ("<", 45)},
            effects={"energy": ("+=", 60)},
            cost=3,
            duration_ticks=5,
            target_type="base",
            description="Rest at the base to restore energy.",
        ),
        Action(
            name="Eat",
            preconditions={"food_cooked": True},
            effects={
                "hunger": ("+=", 55),
                "food_cooked": ("=", False),
                "has_food":   ("=", False),
            },
            cost=2,
            duration_ticks=2,
            target_type="base",
            description="Consume a prepared meal.",
        ),
        Action(
            name="CookMeal",
            preconditions={"has_food": True, "has_fuel": True},
            effects={
                "food_cooked": ("=", True),
                "has_fuel":    ("=", False),
            },
            cost=5,
            duration_ticks=4,
            target_type="base",
            description="Use fuel to cook raw food into a meal.",
        ),
        Action(
            name="Scavenge",
            preconditions={"energy": (">", 10)},
            effects={"has_food": True},
            cost=10,
            duration_ticks=6,
            target_type="food",
            description="Forage the map for raw food.",
        ),
        Action(
            name="CollectFuel",
            preconditions={"energy": (">", 10)},
            effects={"has_fuel": True},
            cost=8,
            duration_ticks=5,
            target_type="fuel",
            description="Retrieve a fuel canister from the environment.",
        ),
        Action(
            name="CollectScrap",
            preconditions={"energy": (">", 15)},
            effects={"has_scrap": True},
            cost=9,
            duration_ticks=5,
            target_type="scrap",
            description="Collect scrap metal for base repairs.",
        ),
        Action(
            name="RepairBase",
            preconditions={"has_scrap": True},
            effects={
                "has_scrap":      ("=", False),
                "base_integrity": ("+=", 25),
            },
            cost=12,
            duration_ticks=6,
            target_type="base",
            description="Use scrap to patch structural damage.",
        ),
        Action(
            name="Socialize",
            preconditions={"social": ("<", 50)},
            effects={"social": ("+=", 35)},
            cost=4,
            duration_ticks=4,
            target_type="npc",
            description="Interact with a nearby crew member.",
        ),
    ]
