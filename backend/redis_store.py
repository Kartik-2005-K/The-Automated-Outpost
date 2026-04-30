"""
redis_store.py — Redis world-state cache with graceful in-memory fallback.

If Redis is unreachable, all calls silently fall back to an in-process dict.
This allows running the backend without Docker.
"""
from __future__ import annotations
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

_fallback_store: dict = {}
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True, socket_connect_timeout=1)
        r.ping()
        _redis_client = r
        logger.info("✅ Redis connected")
        return r
    except Exception:
        logger.warning("⚠️  Redis unavailable — using in-memory fallback")
        return None


def set_world_state(state_dict: dict) -> None:
    r = _get_redis()
    payload = json.dumps(state_dict)
    if r:
        try:
            r.set("outpost:world", payload, ex=3600)
            r.publish("outpost:events", payload)
            return
        except Exception as e:
            logger.warning(f"Redis write failed: {e}")
    _fallback_store["outpost:world"] = payload


def get_world_state() -> Optional[dict]:
    r = _get_redis()
    if r:
        try:
            raw = r.get("outpost:world")
            return json.loads(raw) if raw else None
        except Exception:
            pass
    raw = _fallback_store.get("outpost:world")
    return json.loads(raw) if raw else None


def set_key(key: str, value: Any) -> None:
    r = _get_redis()
    payload = json.dumps(value)
    if r:
        try:
            r.set(f"outpost:{key}", payload, ex=3600)
            return
        except Exception:
            pass
    _fallback_store[f"outpost:{key}"] = payload


def get_key(key: str) -> Any:
    r = _get_redis()
    if r:
        try:
            raw = r.get(f"outpost:{key}")
            return json.loads(raw) if raw else None
        except Exception:
            pass
    raw = _fallback_store.get(f"outpost:{key}")
    return json.loads(raw) if raw else None
