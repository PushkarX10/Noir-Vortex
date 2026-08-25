"""
The Loop — Approval Gate Logic
Handles human-in-the-loop approval at each stage of the pipeline.
Serializes agent output for review, processes approve/reject/revision actions.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ApprovalGate:
    """
    Manages approval gates between agents in the pipeline.
    Each gate pauses execution and waits for human review.
    """

    # Which agents require approval before handoff
    GATES = {
        "researcher": {
            "label": "Research Review",
            "description": "Review discovered trends, content ideas, and viral references",
            "next_agent": "hook_writer",
            "review_fields": ["trends", "content_ideas", "viral_references"],
        },
        "hook_writer": {
            "label": "Hook Review",
            "description": "Review generated hooks, select winners, approve or revise",
            "next_agent": "script_writer",
            "review_fields": ["hooks", "selected_hook"],
        },
        "script_writer": {
            "label": "Script Review",
            "description": "Review full scripts, captions, and hashtag packs",
            "next_agent": "designer",
            "review_fields": ["script", "captions", "hashtags"],
        },
        "designer": {
            "label": "Design Review",
            "description": "Review design briefs, visual specs, and AI image prompts",
            "next_agent": "publisher",
            "review_fields": ["design_briefs", "design_assets"],
        },
    }

    @classmethod
    def get_gate_for_agent(cls, agent_name: str) -> dict | None:
        """Get the approval gate config for a given agent."""
        return cls.GATES.get(agent_name)

    @classmethod
    def get_review_data(cls, agent_name: str, state: dict) -> dict:
        """
        Extract the relevant data for human review from the pipeline state.
        Returns a structured review payload.
        """
        gate = cls.GATES.get(agent_name, {})
        review_fields = gate.get("review_fields", [])

        review_data = {
            "gate": gate.get("label", f"{agent_name} Review"),
            "description": gate.get("description", ""),
            "agent": agent_name,
            "cycle_number": state.get("cycle_number", 0),
            "content": {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        for field in review_fields:
            value = state.get(field, None)
            if value:
                review_data["content"][field] = value

        return review_data

    @classmethod
    def process_approval(cls, agent_name: str, action: str, feedback: str = "") -> dict:
        """
        Process a human approval action.

        Args:
            agent_name: Which agent's output is being reviewed
            action: "approve", "reject", or "revision_requested"
            feedback: Optional human feedback/comments

        Returns:
            State update dict to merge into pipeline state.
        """
        gate = cls.GATES.get(agent_name, {})

        if action == "approve":
            logger.info(f"[ApprovalGate] {agent_name} output APPROVED")
            return {
                "approval_status": "approved",
                "human_feedback": feedback,
                "updated_at": datetime.utcnow().isoformat(),
            }

        elif action == "reject":
            logger.info(f"[ApprovalGate] {agent_name} output REJECTED: {feedback}")
            return {
                "approval_status": "rejected",
                "human_feedback": feedback or "Output rejected. Please revise.",
                "updated_at": datetime.utcnow().isoformat(),
            }

        elif action == "revision_requested":
            logger.info(f"[ApprovalGate] {agent_name} output REVISION REQUESTED: {feedback}")
            return {
                "approval_status": "revision_requested",
                "human_feedback": feedback or "Please revise based on feedback.",
                "updated_at": datetime.utcnow().isoformat(),
            }

        else:
            logger.warning(f"[ApprovalGate] Unknown action '{action}' for {agent_name}")
            return {
                "approval_status": "pending",
                "human_feedback": "",
                "updated_at": datetime.utcnow().isoformat(),
            }

    @classmethod
    def needs_approval(cls, agent_name: str) -> bool:
        """Check if an agent requires approval before handoff."""
        return agent_name in cls.GATES

    @classmethod
    def get_all_gates(cls) -> list[dict]:
        """Get all configured approval gates with their labels."""
        return [
            {
                "agent": agent_name,
                "label": config["label"],
                "description": config["description"],
                "next_agent": config["next_agent"],
            }
            for agent_name, config in cls.GATES.items()
        ]
