"""
goap/planner.py — A*-based GOAP planner.

The planner searches a graph where:
  - Each NODE is a snapshot of the world state (dict)
  - Each EDGE is an action whose preconditions are satisfied
  - g_cost = sum of action costs so far
  - h_cost = number of goal conditions not yet satisfied (admissible heuristic)

Returns the cheapest action sequence that satisfies the given goal's desired_state.
"""
from __future__ import annotations
import heapq
import copy
from typing import List, Dict, Any, Optional

from goap.actions import Action, get_all_actions
from goap.goals import Goal


class PlannerNode:
    __slots__ = ("state", "plan", "g", "f")

    def __init__(self, state: Dict, plan: List[Action], g: float, h: float):
        self.state = state
        self.plan  = plan
        self.g     = g
        self.f     = g + h

    def __lt__(self, other: "PlannerNode"):
        return self.f < other.f


def _heuristic(state: Dict, goal: Goal) -> float:
    """Count unsatisfied goal conditions."""
    unmet = 0
    for key, condition in goal.desired_state.items():
        if isinstance(condition, tuple):
            op, val = condition
            actual = state.get(key, 0)
            if op == ">"  and not (actual > val):  unmet += 1
            if op == ">=" and not (actual >= val):  unmet += 1
            if op == "<"  and not (actual < val):   unmet += 1
            if op == "<=" and not (actual <= val):  unmet += 1
        else:
            if state.get(key) != condition:
                unmet += 1
    return float(unmet)


def _goal_satisfied(state: Dict, goal: Goal) -> bool:
    return goal.is_satisfied(state)


def plan(
    npc_state: Dict[str, Any],
    goal: Goal,
    actions: Optional[List[Action]] = None,
    max_iterations: int = 200,
) -> List[Action]:
    """
    Run A* GOAP planning.
    
    Args:
        npc_state: Flattened dict of NPC + world state flags.
        goal:      Target Goal object.
        actions:   Available actions (defaults to full library).
        max_iterations: Safety cap to prevent runaway search.

    Returns:
        Ordered list of Action objects forming the cheapest plan,
        or [] if no plan is found.
    """
    if actions is None:
        actions = get_all_actions()

    start_state = copy.copy(npc_state)
    start_node  = PlannerNode(
        state=start_state,
        plan=[],
        g=0.0,
        h=_heuristic(start_state, goal),
    )

    open_heap: List[PlannerNode] = [start_node]
    iterations = 0

    while open_heap and iterations < max_iterations:
        iterations += 1
        current = heapq.heappop(open_heap)

        # Goal reached?
        if _goal_satisfied(current.state, goal):
            return current.plan

        # Expand applicable actions
        for action in actions:
            if not action.is_applicable(current.state):
                continue

            new_state = action.apply(current.state)
            new_plan  = current.plan + [action]
            new_g     = current.g + action.cost
            new_h     = _heuristic(new_state, goal)

            child = PlannerNode(
                state=new_state,
                plan=new_plan,
                g=new_g,
                h=new_h,
            )
            heapq.heappush(open_heap, child)

    # No plan found — return Idle
    idle = next((a for a in actions if a.name == "Idle"), None)
    return [idle] if idle else []


def plan_for_npc(
    npc,
    world_state,
    goal: Goal,
    social_memory=None,
) -> List[Action]:
    """
    Convenience wrapper: builds a flat state dict from NPC + WorldState,
    optionally modifies action costs using social memory scores, then plans.
    """
    # Build flat state snapshot
    state: Dict[str, Any] = {
        "energy":         npc.stats.energy,
        "hunger":         npc.stats.hunger,
        "social":         npc.stats.social,
        "has_food":       npc.has_food,
        "has_fuel":       npc.has_fuel,
        "has_scrap":      npc.has_scrap,
        "food_cooked":    npc.food_cooked,
        "base_integrity": world_state.base_integrity,
    }

    # Clone actions; adjust Socialize cost via social memory
    actions = copy.deepcopy(get_all_actions())
    if social_memory is not None:
        for action in actions:
            if action.name == "Socialize":
                # Average social score with all other NPCs
                scores = list(npc.social_scores.values())
                if scores:
                    avg_score = sum(scores) / len(scores)
                    # Hostile history → higher cost (less likely to socialize)
                    action.cost = max(2, action.cost * (1 - avg_score * 0.5))

    return plan(state, goal, actions)
