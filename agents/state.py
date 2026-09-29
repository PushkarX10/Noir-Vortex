"""
Noir -- Shared Pipeline State
TypedDict defining the full state schema that flows through Noir.
Every agent reads from and writes to this shared state.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Any, Optional
from typing_extensions import TypedDict


def _merge_lists(left: list, right: list) -> list:
    """Reducer: merge two lists (append right to left, no duplicates by id)."""
    if not right:
        return left
    existing_ids = {item.get("id") for item in left if isinstance(item, dict) and "id" in item}
    merged = list(left)
    for item in right:
        if isinstance(item, dict) and item.get("id") in existing_ids:
            # Update existing item
            for i, existing in enumerate(merged):
                if isinstance(existing, dict) and existing.get("id") == item["id"]:
                    merged[i] = {**existing, **item}
                    break
        else:
            merged.append(item)
    return merged


def _merge_dicts(left: dict, right: dict) -> dict:
    """Reducer: deep merge two dicts."""
    if not right:
        return left
    merged = dict(left)
    merged.update(right)
    return merged


def _replace(left: Any, right: Any) -> Any:
    """Reducer: simply replace with the newer value."""
    return right if right is not None else left


class PipelineState(TypedDict, total=False):
    """
    Full pipeline state flowing through Noir.
    Each agent reads relevant fields and writes its outputs.
    """

    # --- Research Outputs (Agent 01) ---
    trends: Annotated[list[dict], _merge_lists]
    content_ideas: Annotated[list[dict], _merge_lists]
    viral_references: Annotated[list[dict], _merge_lists]

    # --- Hook Outputs (Agent 02) ---
    hooks: Annotated[list[dict], _merge_lists]
    selected_hook: Annotated[dict, _merge_dicts]

    # --- Script Outputs (Agent 03) ---
    script: Annotated[dict, _merge_dicts]
    captions: Annotated[list[str], _merge_lists]
    hashtags: Annotated[list[str], _merge_lists]

    # --- Design Outputs (Agent 04) ---
    design_briefs: Annotated[list[dict], _merge_lists]
    design_assets: Annotated[list[str], _merge_lists]

    # --- Publishing Outputs (Agent 07) ---
    publish_schedule: Annotated[dict, _merge_dicts]
    publish_results: Annotated[list[dict], _merge_lists]

    # --- Analytics Outputs (Agent 05) ---
    analytics: Annotated[dict, _merge_dicts]
    insights: Annotated[list[str], _merge_lists]

    # --- Sentinel Outputs (Agent 08 -- Buzz integration) ---
    sentinel_scores: Annotated[dict, _merge_dicts]
    audit_trail: Annotated[list[dict], _merge_lists]

    # --- Collaborator Outputs (Agent 09 -- Buzz integration) ---
    context_briefs: Annotated[dict, _merge_dicts]
    cross_agent_insights: Annotated[list[dict], _merge_lists]
    cycle_memory: Annotated[dict, _merge_dicts]

    # --- Automator Outputs (Agent 10 -- Buzz integration) ---
    workflow_definitions: Annotated[list[dict], _merge_lists]
    schedule_recommendations: Annotated[list[dict], _merge_lists]
    automation_insights: Annotated[list[str], _merge_lists]

    # --- Pipeline Control ---
    current_agent: str
    approval_status: str          # "pending" | "approved" | "rejected" | "revision_requested"
    human_feedback: str
    cycle_number: int
    error_message: str
    created_at: str
    updated_at: str


def initial_state(cycle_number: int = 1) -> dict:
    """Create a fresh initial pipeline state."""
    now = datetime.utcnow().isoformat()
    return {
        "trends": [],
        "content_ideas": [],
        "viral_references": [],
        "hooks": [],
        "selected_hook": {},
        "script": {},
        "captions": [],
        "hashtags": [],
        "design_briefs": [],
        "design_assets": [],
        "publish_schedule": {},
        "publish_results": [],
        "analytics": {},
        "insights": [],
        # Buzz integration fields
        "sentinel_scores": {},
        "audit_trail": [],
        "context_briefs": {},
        "cross_agent_insights": [],
        "cycle_memory": {},
        "workflow_definitions": [],
        "schedule_recommendations": [],
        "automation_insights": [],
        # Pipeline control
        "current_agent": "researcher",
        "approval_status": "",
        "human_feedback": "",
        "cycle_number": cycle_number,
        "error_message": "",
        "created_at": now,
        "updated_at": now,
    }


def state_summary(state: dict) -> dict:
    """Generate a human-readable summary of the current pipeline state."""
    return {
        "current_agent": state.get("current_agent", "unknown"),
        "approval_status": state.get("approval_status", ""),
        "cycle": state.get("cycle_number", 0),
        "trends_count": len(state.get("trends", [])),
        "ideas_count": len(state.get("content_ideas", [])),
        "hooks_count": len(state.get("hooks", [])),
        "scripts_count": len(state.get("scripts", [])) if state.get("scripts") else (1 if state.get("script") else 0),
        "has_script": bool(state.get("script")),
        "designs_count": len(state.get("design_assets", [])) or len(state.get("design_briefs", [])),
        "published_count": len(state.get("publish_results", [])),
        "has_analytics": bool(state.get("analytics")),
        # Buzz integration summaries
        "sentinel_scores": state.get("sentinel_scores", {}),
        "audit_entries": len(state.get("audit_trail", [])),
        "active_workflows": len(state.get("workflow_definitions", [])),
        "has_context_briefs": bool(state.get("context_briefs")),
        "error": state.get("error_message", ""),
        "updated_at": state.get("updated_at", ""),
    }
