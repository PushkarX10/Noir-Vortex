"""
Noir -- Agent Context Store
Persistent cross-run memory for agents.

Inspired by Buzz's agent session pooling (buzz-acp/pool.rs) and
agent handoff system (buzz-agent/handoff.rs).  Provides agents with
persistent memory across pipeline cycles, enabling trend tracking,
learning from past successes/failures, and cross-agent context sharing.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ContextStore:
    """
    Persistent agent memory / context store.

    Each agent gets its own memory namespace plus access to a shared
    cross-agent namespace.  Data is persisted to a JSON file on disk.
    """

    def __init__(self, persist_path: str = "./data/context_store.json"):
        self._persist_path = persist_path
        self._store: dict[str, dict] = {
            "_shared": {
                "cycle_count": 0,
                "total_runs": 0,
                "last_run": None,
                "cumulative_insights": [],
            },
        }
        self._load()

    # ------------------------------------------------------------------
    # Agent-scoped memory
    # ------------------------------------------------------------------

    def get(self, agent: str, key: str, default: Any = None) -> Any:
        """Get a value from an agent's memory namespace."""
        ns = self._store.get(agent, {})
        return ns.get(key, default)

    def set(self, agent: str, key: str, value: Any) -> None:
        """Set a value in an agent's memory namespace."""
        if agent not in self._store:
            self._store[agent] = {}
        self._store[agent][key] = value
        self._save()

    def append(self, agent: str, key: str, value: Any, max_items: int = 100) -> None:
        """Append to a list in an agent's memory, with bounded size."""
        if agent not in self._store:
            self._store[agent] = {}
        if key not in self._store[agent]:
            self._store[agent][key] = []
        lst = self._store[agent][key]
        lst.append(value)
        if len(lst) > max_items:
            self._store[agent][key] = lst[-max_items:]
        self._save()

    def get_agent_memory(self, agent: str) -> dict:
        """Get the full memory namespace for an agent."""
        return dict(self._store.get(agent, {}))

    def clear_agent(self, agent: str) -> None:
        """Clear all memory for an agent."""
        self._store.pop(agent, None)
        self._save()

    # ------------------------------------------------------------------
    # Shared cross-agent memory
    # ------------------------------------------------------------------

    def get_shared(self, key: str, default: Any = None) -> Any:
        """Get a value from the shared cross-agent namespace."""
        return self._store.get("_shared", {}).get(key, default)

    def set_shared(self, key: str, value: Any) -> None:
        """Set a value in the shared namespace."""
        if "_shared" not in self._store:
            self._store["_shared"] = {}
        self._store["_shared"][key] = value
        self._save()

    def increment_shared(self, key: str, amount: int = 1) -> int:
        """Increment a counter in the shared namespace."""
        current = self.get_shared(key, 0)
        new_val = current + amount
        self.set_shared(key, new_val)
        return new_val

    # ------------------------------------------------------------------
    # Cycle lifecycle
    # ------------------------------------------------------------------

    def begin_cycle(self, cycle_number: int) -> None:
        """Mark the start of a new pipeline cycle."""
        self.set_shared("current_cycle", cycle_number)
        self.set_shared("last_run", datetime.utcnow().isoformat())
        self.increment_shared("total_runs")
        logger.info(
            f"[ContextStore] Cycle #{cycle_number} started "
            f"(total runs: {self.get_shared('total_runs')})"
        )

    def end_cycle(self, cycle_number: int, summary: dict) -> None:
        """Record end-of-cycle summary to shared memory."""
        self.set_shared("cycle_count", cycle_number)
        self.append("_shared", "cycle_summaries", {
            "cycle": cycle_number,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": summary,
        }, max_items=50)
        logger.info(f"[ContextStore] Cycle #{cycle_number} completed")

    # ------------------------------------------------------------------
    # Trend & insight memory (cross-cycle learning)
    # ------------------------------------------------------------------

    def record_trend(self, trend: dict) -> None:
        """Record a trend for cross-cycle tracking."""
        self.append("_shared", "trend_history", {
            "title": trend.get("title", ""),
            "platform": trend.get("platform", ""),
            "virality_score": trend.get("virality_score", 0),
            "discovered_at": trend.get("discovered_at", datetime.utcnow().isoformat()),
        }, max_items=200)

    def get_trend_history(self, limit: int = 50) -> list[dict]:
        """Get recent trend history for cross-cycle analysis."""
        history = self.get_shared("trend_history", [])
        return history[-limit:]

    def record_insight(self, insight: str, source_agent: str) -> None:
        """Record a learning insight."""
        self.append("_shared", "cumulative_insights", {
            "insight": insight,
            "source": source_agent,
            "recorded_at": datetime.utcnow().isoformat(),
        }, max_items=100)

    def get_insights(self, limit: int = 20) -> list[dict]:
        """Get recent cumulative insights."""
        insights = self.get_shared("cumulative_insights", [])
        return insights[-limit:]

    # ------------------------------------------------------------------
    # Agent handoff context (inspired by buzz-agent/handoff.rs)
    # ------------------------------------------------------------------

    def prepare_handoff(self, from_agent: str, to_agent: str, context: dict) -> dict:
        """
        Prepare a context handoff between agents.
        Stores the handoff data and returns a reference.
        """
        handoff = {
            "from": from_agent,
            "to": to_agent,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.set(to_agent, f"handoff_from_{from_agent}", handoff)
        logger.info(f"[ContextStore] Handoff prepared: {from_agent} -> {to_agent}")
        return handoff

    def receive_handoff(self, agent: str, from_agent: str) -> Optional[dict]:
        """Receive a context handoff from another agent."""
        handoff = self.get(agent, f"handoff_from_{from_agent}")
        if handoff:
            logger.info(f"[ContextStore] Handoff received: {from_agent} -> {agent}")
        return handoff

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Get memory store statistics."""
        return {
            "total_namespaces": len(self._store),
            "agents": [k for k in self._store if k != "_shared"],
            "total_runs": self.get_shared("total_runs", 0),
            "cycle_count": self.get_shared("cycle_count", 0),
            "trend_history_size": len(self.get_shared("trend_history", [])),
            "insights_count": len(self.get_shared("cumulative_insights", [])),
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        """Persist store to disk."""
        try:
            path = Path(self._persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(self._store, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"[ContextStore] Failed to persist: {e}")

    def _load(self) -> None:
        """Load store from disk."""
        try:
            path = Path(self._persist_path)
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                self._store.update(data)
                logger.info(
                    f"[ContextStore] Loaded {len(self._store)} namespaces "
                    f"from {self._persist_path}"
                )
        except Exception as e:
            logger.error(f"[ContextStore] Failed to load: {e}")
