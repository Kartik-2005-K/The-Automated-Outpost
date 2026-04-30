"""
pathfinding/grid.py — Static grid representation and walkability queries.
"""
from __future__ import annotations
from typing import List, Tuple
from world_state import GRID_W, GRID_H


def idx(x: int, y: int) -> int:
    return y * GRID_W + x


def is_walkable(grid: List[int], x: int, y: int) -> bool:
    if x < 0 or y < 0 or x >= GRID_W or y >= GRID_H:
        return False
    return grid[idx(x, y)] == 1


def get_neighbors(grid: List[int], x: int, y: int) -> List[Tuple[int, int]]:
    """4-directional neighbors that are walkable."""
    candidates = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    return [(nx, ny) for nx, ny in candidates if is_walkable(grid, nx, ny)]
