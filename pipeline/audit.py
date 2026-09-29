"""
Noir -- Pipeline Audit Trail
Hash-chain tamper-evident logging for pipeline decisions.

Inspired by buzz-audit: every agent output, approval decision, and
state change is recorded in a linked chain of SHA-256 hashes.
If any entry is modified after the fact, the chain breaks.
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class AuditEntry:
    """A single entry in the audit chain."""

    __slots__ = (
        "id", "sequence", "event_type", "agent", "cycle",
        "data", "timestamp", "hash", "prev_hash",
    )

    def __init__(
        self,
        entry_id: str,
        sequence: int,
        event_type: str,
        agent: str,
        cycle: int,
        data: dict,
        timestamp: str,
        entry_hash: str = "",
        prev_hash: str = "",
    ):
        self.id = entry_id
        self.sequence = sequence
        self.event_type = event_type
        self.agent = agent
        self.cycle = cycle
        self.data = data
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        # Compute hash if not provided
        if entry_hash:
            self.hash = entry_hash
        else:
            canonical = json.dumps(
                {
                    "id": self.id,
                    "seq": self.sequence,
                    "type": self.event_type,
                    "agent": self.agent,
                    "cycle": self.cycle,
                    "data": self.data,
                    "ts": self.timestamp,
                    "prev": self.prev_hash,
                },
                sort_keys=True,
            )
            self.hash = _sha256(canonical)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "agent": self.agent,
            "cycle": self.cycle,
            "data": self.data,
            "timestamp": self.timestamp,
            "hash": self.hash,
            "prev_hash": self.prev_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AuditEntry":
        return cls(
            entry_id=d["id"],
            sequence=d["sequence"],
            event_type=d["event_type"],
            agent=d["agent"],
            cycle=d["cycle"],
            data=d.get("data", {}),
            timestamp=d["timestamp"],
            entry_hash=d.get("hash", ""),
            prev_hash=d.get("prev_hash", ""),
        )


class AuditTrail:
    """
    Hash-chain audit trail for the Noir pipeline.

    Every significant pipeline event is appended as an AuditEntry.
    Each entry's hash incorporates the previous entry's hash,
    forming an append-only tamper-evident log.
    """

    # Recognised event types
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    APPROVAL_PENDING = "approval_pending"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_REVISION = "approval_revision"
    SENTINEL_EVAL = "sentinel_eval"
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    WORKFLOW_TRIGGER = "workflow_trigger"

    def __init__(self, persist_path: Optional[str] = None):
        self._chain: list[AuditEntry] = []
        self._persist_path = persist_path

    @property
    def length(self) -> int:
        return len(self._chain)

    @property
    def latest(self) -> Optional[AuditEntry]:
        return self._chain[-1] if self._chain else None

    def append(
        self,
        event_type: str,
        agent: str,
        cycle: int,
        data: dict | None = None,
    ) -> AuditEntry:
        """Append a new entry to the audit chain."""
        import uuid

        prev_hash = self._chain[-1].hash if self._chain else ""
        seq = len(self._chain) + 1

        entry = AuditEntry(
            entry_id=f"audit-{uuid.uuid4().hex[:8]}",
            sequence=seq,
            event_type=event_type,
            agent=agent,
            cycle=cycle,
            data=data or {},
            timestamp=datetime.utcnow().isoformat(),
            prev_hash=prev_hash,
        )
        self._chain.append(entry)

        logger.debug(
            f"[AuditTrail] #{seq} {event_type} ({agent}) "
            f"hash={entry.hash[:12]}..."
        )

        if self._persist_path:
            self._save()

        return entry

    def verify(self) -> tuple[bool, Optional[int]]:
        """
        Verify the integrity of the entire chain.
        Returns (is_valid, first_broken_sequence_or_None).
        """
        for i, entry in enumerate(self._chain):
            expected_prev = self._chain[i - 1].hash if i > 0 else ""
            if entry.prev_hash != expected_prev:
                logger.warning(
                    f"[AuditTrail] Chain broken at sequence {entry.sequence}"
                )
                return False, entry.sequence
        return True, None

    def get_entries(
        self,
        agent: Optional[str] = None,
        event_type: Optional[str] = None,
        cycle: Optional[int] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Query audit entries with optional filters."""
        results = self._chain
        if agent:
            results = [e for e in results if e.agent == agent]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if cycle is not None:
            results = [e for e in results if e.cycle == cycle]
        return [e.to_dict() for e in results[-limit:]]

    def to_list(self) -> list[dict]:
        """Serialize the full chain."""
        return [e.to_dict() for e in self._chain]

    def load_from_list(self, entries: list[dict]) -> None:
        """Restore chain from serialized list."""
        self._chain = [AuditEntry.from_dict(e) for e in entries]

    def _save(self) -> None:
        """Persist to disk."""
        if not self._persist_path:
            return
        try:
            path = Path(self._persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(self.to_list(), indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"[AuditTrail] Failed to persist: {e}")

    def _load(self) -> None:
        """Load from disk."""
        if not self._persist_path:
            return
        try:
            path = Path(self._persist_path)
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                self.load_from_list(data)
                logger.info(f"[AuditTrail] Loaded {len(self._chain)} entries")
        except Exception as e:
            logger.error(f"[AuditTrail] Failed to load: {e}")
