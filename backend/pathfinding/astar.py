"""
pathfinding/astar.py — A* pathfinder with influence-map cost integration.

Influence map values are added to the g_cost of entering each cell,
making dangerous areas "expensive" and causing NPCs to naturally re-route.
"""
from __future__ import annotations
import heapq
from typing import List, Tuple, Optional, Dict

from world_state import GRID_W, GRID_H
from pathfinding.grid import idx, is_walkable, get_neighbors

DANGER_WEIGHT = 4.0   # how much influence map danger inflates movement cost


class AStarNode:
    __slots__ = ("x", "y", "g", "f", "parent")

    def __init__(self, x: int, y: int, g: float, h: float, parent=None):
        self.x = x
        self.y = y
        self.g = g
        self.f = g + h
        self.parent = parent

    def __lt__(self, other: "AStarNode"):
        return self.f < other.f


def _manhattan(ax: int, ay: int, bx: int, by: int) -> float:
    return float(abs(ax - bx) + abs(ay - by))


def astar(
    grid: List[int],
    influence_map: List[float],
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> List[Tuple[int, int]]:
    """
    Find the cheapest path from start to goal on the given grid,
    weighted by the influence map.

    Returns a list of (x, y) waypoints including start and goal,
    or [] if no path exists.
    """
    sx, sy = start
    gx, gy = goal

    if not is_walkable(grid, sx, sy) or not is_walkable(grid, gx, gy):
        return []

    if start == goal:
        return [start]

    open_heap: List[AStarNode] = []
    start_node = AStarNode(sx, sy, 0.0, _manhattan(sx, sy, gx, gy))
    heapq.heappush(open_heap, start_node)

    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {(sx, sy): None}
    g_scores: Dict[Tuple[int, int], float] = {(sx, sy): 0.0}

    while open_heap:
        current = heapq.heappop(open_heap)
        cx, cy = current.x, current.y

        if (cx, cy) == (gx, gy):
            return _reconstruct(came_from, (gx, gy))

        for nx, ny in get_neighbors(grid, cx, cy):
            danger = influence_map[idx(nx, ny)]
            step_cost = 1.0 + danger * DANGER_WEIGHT
            tentative_g = g_scores[(cx, cy)] + step_cost

            if (nx, ny) not in g_scores or tentative_g < g_scores[(nx, ny)]:
                g_scores[(nx, ny)] = tentative_g
                h = _manhattan(nx, ny, gx, gy)
                node = AStarNode(nx, ny, tentative_g, h)
                came_from[(nx, ny)] = (cx, cy)
                heapq.heappush(open_heap, node)

    return []   # No path found


def _reconstruct(
    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]],
    current: Tuple[int, int],
) -> List[Tuple[int, int]]:
    path = []
    while current is not None:
        path.append(current)
        current = came_from.get(current)
    path.reverse()
    return path
