"""
goap/goals.py — Goal definitions for each NPC.

Goals are evaluated every tick; the highest-priority UNSATISFIED goal
triggers the GOAP planner to compute a new action plan.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Callable


@dataclass
class Goal:
    name: str
    priority: int          # lower number = checked first
    desired_state: Dict[str, Any]
    is_satisfied: Callable[[Dict[str, Any]], bool]
    description: str = ""


def _stat_ok(key: str, threshold: float, above: bool = True):
    """Factory: returns a satisfaction check lambda."""
    if above:
        return lambda s: s.get(key, 0) >= threshold
    else:
        return lambda s: s.get(key, 0) <= threshold


ALL_GOALS: list[Goal] = [
    Goal(
        name="Survive",
        priority=1,
        desired_state={"hunger": (">", 30)},
        is_satisfied=lambda s: s.get("hunger", 0) > 30,
        description="Keep hunger above critical level.",
    ),
    Goal(
        name="Rest",
        priority=2,
        desired_state={"energy": (">", 40)},
        is_satisfied=lambda s: s.get("energy", 0) > 40,
        description="Maintain energy above dangerous low.",
    ),
    Goal(
        name="MaintainSocial",
        priority=3,
        desired_state={"social": (">", 30)},
        is_satisfied=lambda s: s.get("social", 0) > 30,
        description="Stay mentally stable through contact.",
    ),
    Goal(
        name="RepairBase",
        priority=4,
        desired_state={"base_integrity": (">", 60)},
        is_satisfied=lambda s: s.get("base_integrity", 100) > 60,
        description="Maintain structural integrity of the outpost.",
    ),
    Goal(
        name="Idle",
        priority=99,
        desired_state={},
        is_satisfied=lambda s: True,   # always satisfied = fallback
        description="No urgent goal. Stand by.",
    ),
]


def select_goal(npc_state: Dict[str, Any]) -> Goal:
    """Return the highest-priority unsatisfied goal."""
    for goal in sorted(ALL_GOALS, key=lambda g: g.priority):
        if not goal.is_satisfied(npc_state):
            return goal
    return ALL_GOALS[-1]  # Idle fallback
