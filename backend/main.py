"""
main.py — FastAPI application entry point for The Automated Outpost.

Architecture:
  - /ws              WebSocket: streams full world state JSON each tick
  - GET  /state      REST: snapshot of current world state
  - POST /event      REST: manually trigger a game event
  - GET  /npc/{id}/plan  REST: debug – show NPC's current GOAP plan
  - GET  /logs       REST: recent social interaction log

A background asyncio task runs the simulation at ~1 tick/second.
Each tick:
  1. Decay NPC stats
  2. Tick down active events; spawn new random ones
  3. Apply influence map (decay + re-stamp event sources)
  4. For each NPC: evaluate goals → GOAP plan → move along A* path → execute action
  5. Check NPC proximity for social interactions
  6. Broadcast world state over WebSocket
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import uuid
from typing import Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from world_state import (
    WorldState, NPC, Resource, GameEvent,
    build_initial_world, GRID_W, GRID_H,
    RESOURCE_FOOD, RESOURCE_FUEL, RESOURCE_SCRAP,
)
from goap.actions import get_all_actions
from goap.goals import ALL_GOALS, select_goal
from goap.planner import plan_for_npc
from pathfinding.astar import astar
from pathfinding.influence import InfluenceMap
from memory.social_memory import SocialMemory
from memory.events_log import EventsLog
import redis_store

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────
app = FastAPI(title="Automated Outpost Brain", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────
# Global singletons
# ──────────────────────────────────────────────────────────────
world: WorldState = build_initial_world()
influence_map: InfluenceMap = InfluenceMap()
social_memory: SocialMemory = SocialMemory()
events_log: EventsLog = EventsLog()
connected_clients: Set[WebSocket] = set()

TICK_RATE_SECONDS = 1.0        # simulation speed
NPC_MOVE_SPEED    = 0.8        # tiles per tick (fractional movement)
SOCIAL_DIST       = 3.0        # tiles within which NPCs can socialize
BASE_POSITION     = [14, 14]   # centre of the map — the "base"

# ──────────────────────────────────────────────────────────────
# Pydantic models for REST
# ──────────────────────────────────────────────────────────────
class EventRequest(BaseModel):
    event_type: str   # "power_failure" | "toxic_spill" | "food_shortage" | "meteor_strike"


PREDEFINED_EVENTS = {
    "power_failure": {
        "name": "⚡ Power Failure",
        "description": "Primary power grid offline. Energy regeneration halved.",
        "position": None,
        "duration_ticks": 20,
        "danger_strength": 0.0,
        "effect": "power_failure",
    },
    "toxic_spill": {
        "name": "☠️ Toxic Spill",
        "description": "Chemical leak detected at sector. Area is hazardous.",
        "position": [15, 15],
        "duration_ticks": 25,
        "danger_strength": 0.9,
        "effect": "danger_zone",
    },
    "food_shortage": {
        "name": "🥫 Food Shortage",
        "description": "Food reserves critically low. NPCs must scavenge.",
        "position": None,
        "duration_ticks": 15,
        "danger_strength": 0.0,
        "effect": "food_shortage",
    },
    "meteor_strike": {
        "name": "☄️ Meteor Strike",
        "description": "Meteor impact at sector! Structural damage sustained.",
        "position": [random.randint(5, 25), random.randint(5, 25)],
        "duration_ticks": 30,
        "danger_strength": 1.0,
        "effect": "damage_base",
    },
    "dust_storm": {
        "name": "🌪️ Dust Storm",
        "description": "Visibility zero. Movement cost increased across all sectors.",
        "position": None,
        "duration_ticks": 18,
        "danger_strength": 0.0,
        "effect": "dust_storm",
    },
}


# ──────────────────────────────────────────────────────────────
# WebSocket manager
# ──────────────────────────────────────────────────────────────
async def broadcast(data: dict):
    """Send world state to all connected WebSocket clients."""
    payload = json.dumps(data)
    dead: Set[WebSocket] = set()
    for ws in connected_clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    connected_clients.difference_update(dead)


# ──────────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────────
def dist(a: List[float], b: List[float]) -> float:
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def find_nearest_resource(npc: NPC, rtype: str) -> Optional[Resource]:
    candidates = [r for r in world.resources if r.type == rtype and r.quantity > 0]
    if not candidates:
        return None
    return min(candidates, key=lambda r: dist(npc.position, r.position))


def npc_grid_pos(npc: NPC):
    return (int(round(npc.position[0])), int(round(npc.position[1])))


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def respawn_resources():
    """Ensure there's always some food/fuel/scrap on the map."""
    for rtype in [RESOURCE_FOOD, RESOURCE_FUEL, RESOURCE_SCRAP]:
        count = sum(1 for r in world.resources if r.type == rtype and r.quantity > 0)
        if count < 2:
            x = random.randint(3, GRID_W-3)
            y = random.randint(3, GRID_H-3)
            # Avoid wall cells
            if world.grid[y * GRID_W + x] == 1:
                world.resources.append(Resource(
                    id=f"res_{uuid.uuid4().hex[:6]}",
                    type=rtype,
                    position=[float(x), float(y)],
                    quantity=random.randint(3, 6),
                ))


# ──────────────────────────────────────────────────────────────
# NPC AI tick
# ──────────────────────────────────────────────────────────────
def tick_npc(npc: NPC):
    """Run one simulation tick for a single NPC."""

    # ── 1. Stat decay ──
    npc.stats.decay(world.tick)

    # ── 2. Goal selection ──
    flat_state = {
        "energy":         npc.stats.energy,
        "hunger":         npc.stats.hunger,
        "social":         npc.stats.social,
        "has_food":       npc.has_food,
        "has_fuel":       npc.has_fuel,
        "has_scrap":      npc.has_scrap,
        "food_cooked":    npc.food_cooked,
        "base_integrity": world.base_integrity,
    }
    goal = select_goal(flat_state)

    # Re-plan if goal changed OR plan is empty (always plan on first tick)
    should_replan = (goal.name != npc.current_goal) or (not npc.current_plan)
    if should_replan:
        npc.current_goal = goal.name
        actions = plan_for_npc(npc, world, goal, social_memory)
        if not actions:
            # Ensure we always have at least Idle as fallback
            idle_actions = [a for a in get_all_actions() if a.name == "Idle"]
            actions = idle_actions
        npc.current_plan = [a.name for a in actions]
        npc.current_action = npc.current_plan[0] if npc.current_plan else "Idle"
        npc.action_progress = 0.0
        npc.status = f"🧠 Planning: {npc.current_goal} → {' → '.join(npc.current_plan[:3])}"
        # Assign movement target
        assign_target(npc, npc.current_action)

    # ── 3. Movement ──
    if npc.path:
        move_along_path(npc)
    elif npc.target_position and dist(npc.position, npc.target_position) > 0.5:
        compute_path(npc)

    # ── 4. Action execution ──
    npc.action_progress = min(1.0, npc.action_progress + (1.0 / get_action_duration(npc.current_action)))

    if npc.action_progress >= 1.0:
        execute_action(npc)
        npc.action_progress = 0.0
        # Advance plan
        if npc.current_plan:
            npc.current_plan.pop(0)
        if npc.current_plan:
            npc.current_action = npc.current_plan[0]
            assign_target(npc, npc.current_action)
        else:
            npc.current_action = "Idle"
            npc.current_goal = "Idle"


def get_action_duration(action_name: str) -> int:
    for a in get_all_actions():
        if a.name == action_name:
            return a.duration_ticks
    return 3


def assign_target(npc: NPC, action_name: str):
    """Set the NPC's movement target based on the action type."""
    npc.path = []
    if action_name in ("Sleep", "Eat", "CookMeal", "RepairBase"):
        npc.target_position = list(BASE_POSITION)
    elif action_name == "Scavenge":
        res = find_nearest_resource(npc, RESOURCE_FOOD)
        npc.target_position = list(res.position) if res else list(BASE_POSITION)
    elif action_name == "CollectFuel":
        res = find_nearest_resource(npc, RESOURCE_FUEL)
        npc.target_position = list(res.position) if res else list(BASE_POSITION)
    elif action_name == "CollectScrap":
        res = find_nearest_resource(npc, RESOURCE_SCRAP)
        npc.target_position = list(res.position) if res else list(BASE_POSITION)
    elif action_name == "Socialize":
        # Move toward the closest other NPC
        others = [n for n in world.npcs if n.id != npc.id]
        if others:
            closest = min(others, key=lambda o: dist(npc.position, o.position))
            npc.target_position = list(closest.position)
    else:
        npc.target_position = None


def compute_path(npc: NPC):
    if npc.target_position is None:
        return
    start = npc_grid_pos(npc)
    goal  = (int(round(npc.target_position[0])), int(round(npc.target_position[1])))
    goal  = (clamp(goal[0], 1, GRID_W-2), clamp(goal[1], 1, GRID_H-2))
    path  = astar(world.grid, influence_map.values, start, goal)
    npc.path = [[float(x), float(y)] for x, y in path]


def move_along_path(npc: NPC):
    """Step the NPC toward the next waypoint."""
    if not npc.path:
        return
    next_wp = npc.path[0]
    dx = next_wp[0] - npc.position[0]
    dy = next_wp[1] - npc.position[1]
    d  = math.sqrt(dx*dx + dy*dy)
    if d < 0.15:
        npc.path.pop(0)
        return
    step = min(NPC_MOVE_SPEED, d)
    npc.position[0] += (dx / d) * step
    npc.position[1] += (dy / d) * step


def execute_action(npc: NPC):
    """Apply the effects of the current action to the world."""
    action_name = npc.current_action
    npc.status = f"✔ {action_name} complete"

    at_base = dist(npc.position, BASE_POSITION) < 3.0

    if action_name == "Sleep":
        npc.stats.energy = min(100, npc.stats.energy + 60)
        npc.status = "😴 Rested"

    elif action_name == "Scavenge":
        res = find_nearest_resource(npc, RESOURCE_FOOD)
        if res and res.quantity > 0:
            res.quantity -= 1
            npc.has_food = True
            npc.status = f"🍎 Scavenged food from {res.id}"
        else:
            npc.status = "🔍 No food found"

    elif action_name == "CollectFuel":
        res = find_nearest_resource(npc, RESOURCE_FUEL)
        if res and res.quantity > 0:
            res.quantity -= 1
            npc.has_fuel = True
            npc.status = f"⛽ Collected fuel from {res.id}"
        else:
            npc.status = "🔍 No fuel found"

    elif action_name == "CollectScrap":
        res = find_nearest_resource(npc, RESOURCE_SCRAP)
        if res and res.quantity > 0:
            res.quantity -= 1
            npc.has_scrap = True
            npc.status = f"🔧 Collected scrap from {res.id}"
        else:
            npc.status = "🔍 No scrap found"

    elif action_name == "CookMeal":
        if npc.has_food and npc.has_fuel:
            npc.food_cooked = True
            npc.has_fuel = False
            npc.status = "🍳 Meal cooked"
        else:
            npc.status = "⚠️ Missing ingredients"

    elif action_name == "Eat":
        if npc.food_cooked:
            npc.stats.hunger = min(100, npc.stats.hunger + 55)
            npc.food_cooked = False
            npc.has_food = False
            npc.status = "🍽️ Ate meal"
        else:
            npc.status = "⚠️ No cooked food"

    elif action_name == "RepairBase":
        if npc.has_scrap:
            world.base_integrity = min(100, world.base_integrity + 25)
            npc.has_scrap = False
            npc.status = "🔨 Repaired base"
        else:
            npc.status = "⚠️ No scrap"

    elif action_name == "Socialize":
        # Find nearest NPC and trigger social event
        others = [n for n in world.npcs if n.id != npc.id]
        if others:
            partner = min(others, key=lambda o: dist(npc.position, o.position))
            if dist(npc.position, partner.position) < SOCIAL_DIST:
                # Retrieve memory score to determine outcome
                score = social_memory.recall(npc.id, partner.id)
                if score >= 0:
                    sentiment = random.uniform(0.3, 1.0)
                    event_type = "greet"
                    desc = f"{npc.name} had a friendly exchange with {partner.name}."
                else:
                    sentiment = random.uniform(-0.8, 0.0)
                    event_type = "argue"
                    desc = f"{npc.name} had a tense interaction with {partner.name}."

                # Random chance of resource sharing
                if random.random() < 0.3 and npc.has_food and not partner.has_food:
                    npc.has_food = False
                    partner.has_food = True
                    sentiment = 0.9
                    event_type = "share"
                    desc = f"{npc.name} shared food with {partner.name}."

                elif random.random() < 0.15:
                    sentiment = -0.6
                    event_type = "refuse"
                    desc = f"{npc.name} refused to share resources with {partner.name}."

                # Store in social memory
                social_memory.store(npc.id, partner.id, desc, sentiment)
                events_log.record(
                    world.tick, npc.id, partner.id,
                    event_type, desc, sentiment
                )

                # Update social scores
                npc.social_scores[partner.id]    = round(sentiment, 2)
                partner.social_scores[npc.id]    = round(sentiment, 2)

                # Boost social stat
                npc.stats.social     = min(100, npc.stats.social + 30)
                partner.stats.social = min(100, partner.stats.social + 15)
                npc.status = f"💬 {desc}"
            else:
                npc.status = "💬 No one nearby"
        else:
            npc.status = "💬 Alone"

    elif action_name == "Idle":
        npc.status = "💤 Idle"


# ──────────────────────────────────────────────────────────────
# Event system
# ──────────────────────────────────────────────────────────────
def apply_event_effects(event: GameEvent):
    """Apply immediate world-state effects of an event."""
    # event.id format: "event_type_hexcode" — extract event_type by stripping last part
    parts = event.id.rsplit("_", 1)
    event_key = parts[0] if len(parts) > 1 else event.id
    spec = PREDEFINED_EVENTS.get(event_key, {})
    etype = spec.get("effect", "")
    if etype == "damage_base":
        world.base_integrity = max(0, world.base_integrity - 30)
        logger.info(f"🔴 Base damaged: integrity={world.base_integrity:.0f}")
    elif etype == "food_shortage":
        for r in world.resources:
            if r.type == RESOURCE_FOOD:
                r.quantity = max(0, r.quantity - 2)


def trigger_event(event_type: str) -> Optional[GameEvent]:
    spec = PREDEFINED_EVENTS.get(event_type)
    if not spec:
        return None
    pos = spec["position"]
    if pos and event_type == "meteor_strike":
        pos = [random.randint(5, 25), random.randint(5, 25)]
    event = GameEvent(
        id=f"{event_type}_{uuid.uuid4().hex[:6]}",
        name=spec["name"],
        description=spec["description"],
        position=pos,
        duration_ticks=spec["duration_ticks"],
        remaining_ticks=spec["duration_ticks"],
        danger_strength=spec["danger_strength"],
    )
    world.events.append(event)
    apply_event_effects(event)
    logger.info(f"🚨 Event triggered: {event.name}")
    return event


def tick_events():
    """Advance event timers; remove expired events."""
    for event in world.events[:]:
        event.remaining_ticks -= 1
        if event.remaining_ticks <= 0:
            world.events.remove(event)
            logger.info(f"✅ Event resolved: {event.name}")


RANDOM_EVENT_CHANCE = 0.03   # 3% per tick


def maybe_random_event():
    if random.random() < RANDOM_EVENT_CHANCE:
        etype = random.choice(list(PREDEFINED_EVENTS.keys()))
        trigger_event(etype)


# ──────────────────────────────────────────────────────────────
# Main simulation tick
# ──────────────────────────────────────────────────────────────
async def simulation_loop():
    logger.info("🚀 Simulation loop started")
    while True:
        await asyncio.sleep(TICK_RATE_SECONDS)
        try:
            world.tick += 1

            # Events
            tick_events()
            maybe_random_event()

            # Influence map: decay then re-stamp active events
            influence_map.decay()
            influence_map.apply_events(world.events)
            world.influence_map = influence_map.as_list()

            # NPC ticks
            for npc in world.npcs:
                tick_npc(npc)

            # Resource respawn
            if world.tick % 15 == 0:
                respawn_resources()

            # Persist to Redis
            state_dict = world.to_dict()
            redis_store.set_world_state(state_dict)

            # Broadcast over WebSocket
            await broadcast(state_dict)

        except Exception as e:
            logger.error(f"Tick error (tick={world.tick}): {e}", exc_info=True)


# ──────────────────────────────────────────────────────────────
# FastAPI lifecycle
# ──────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    asyncio.create_task(simulation_loop())
    logger.info("🌍 World initialised | NPCs: 4 | Grid: 30×30")


# ──────────────────────────────────────────────────────────────
# WebSocket endpoint
# ──────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    logger.info(f"🔌 Client connected | total={len(connected_clients)}")
    # Send immediate snapshot
    await ws.send_text(json.dumps(world.to_dict()))
    try:
        while True:
            await ws.receive_text()   # keep connection alive
    except WebSocketDisconnect:
        connected_clients.discard(ws)
        logger.info("🔌 Client disconnected")


# ──────────────────────────────────────────────────────────────
# REST endpoints
# ──────────────────────────────────────────────────────────────
@app.get("/state")
async def get_state():
    return world.to_dict()


@app.post("/event")
async def post_event(req: EventRequest):
    event = trigger_event(req.event_type)
    if not event:
        return {"error": f"Unknown event type: {req.event_type}"}
    return {"status": "triggered", "event": event.to_dict()}


@app.get("/npc/{npc_id}/plan")
async def get_npc_plan(npc_id: str):
    npc = next((n for n in world.npcs if n.id == npc_id), None)
    if not npc:
        return {"error": "NPC not found"}
    return {
        "id": npc.id,
        "name": npc.name,
        "goal": npc.current_goal,
        "plan": npc.current_plan,
        "current_action": npc.current_action,
        "action_progress": npc.action_progress,
        "status": npc.status,
    }


@app.get("/logs")
async def get_logs():
    return {
        "interactions": [e.to_dict() for e in events_log.recent(20)],
        "total": len(events_log.all_entries()),
    }


@app.get("/events/available")
async def get_available_events():
    return {"events": list(PREDEFINED_EVENTS.keys())}
