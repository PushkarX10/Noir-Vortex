"""
Agent 06: The Manager (Operations)
Core Directive: Run the whole company and route handoffs.
Pipeline: Research → Hooks → Scripts → Design → Publish → Analyze → Repeat
This agent IS the LangGraph — it defines the state machine that orchestrates all other agents.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ManagerAgent:
    """
    Agent 06: The Manager — orchestrates the entire pipeline.
    
    Unlike other agents, the Manager doesn't generate content via LLM.
    Instead, it defines the routing logic, manages handoffs, monitors
    agent outputs, and ensures daily publishing on time.
    
    The actual graph definition is in pipeline/graph.py — the Manager
    is the logical "owner" of that graph.
    """

    def __init__(self):
        self.name = "manager"
        self.display_name = "The Manager"
        self.department = "Operations"

    def get_pipeline_sequence(self) -> list[str]:
        """The canonical pipeline sequence."""
        return [
            "researcher",
            "hook_writer",
            "script_writer",
            "designer",
            "publisher",
            "analyst",
        ]

    def get_agent_after(self, current: str) -> str | None:
        """Get the next agent in the pipeline after the current one."""
        sequence = self.get_pipeline_sequence()
        try:
            idx = sequence.index(current)
            if idx + 1 < len(sequence):
                return sequence[idx + 1]
            return None  # End of pipeline
        except ValueError:
            return None

    def route_approval(self, state: dict) -> str:
        """
        Route based on approval status.
        Called by the LangGraph conditional edge after each approval gate.
        
        Returns the name of the next node to execute.
        """
        approval_status = state.get("approval_status", "")
        current_agent = state.get("current_agent", "")

        if approval_status == "approved":
            next_agent = self.get_agent_after(current_agent)
            if next_agent:
                logger.info(f"[{self.display_name}] Approved! Routing {current_agent} → {next_agent}")
                return next_agent
            else:
                logger.info(f"[{self.display_name}] Pipeline complete! Starting next cycle.")
                return "end"

        elif approval_status == "rejected":
            logger.info(f"[{self.display_name}] Rejected. Routing back to {current_agent} for revision.")
            return current_agent

        elif approval_status == "revision_requested":
            logger.info(f"[{self.display_name}] Revision requested. Routing back to {current_agent}.")
            return current_agent

        else:
            # Pending — stay at approval gate
            logger.info(f"[{self.display_name}] Awaiting approval for {current_agent}.")
            return "approval_gate"

    def get_status_report(self, state: dict) -> dict:
        """Generate a manager's status report of the pipeline."""
        sequence = self.get_pipeline_sequence()
        current = state.get("current_agent", "")

        agent_statuses = {}
        current_idx = sequence.index(current) if current in sequence else -1

        for i, agent_name in enumerate(sequence):
            if i < current_idx:
                status = "completed"
            elif i == current_idx:
                approval = state.get("approval_status", "")
                if approval == "pending":
                    status = "awaiting_approval"
                elif approval in ("rejected", "revision_requested"):
                    status = "revision_in_progress"
                else:
                    status = "active"
            else:
                status = "queued"

            agent_statuses[agent_name] = status

        return {
            "cycle_number": state.get("cycle_number", 0),
            "current_agent": current,
            "approval_status": state.get("approval_status", ""),
            "agent_statuses": agent_statuses,
            "pipeline_progress": f"{current_idx + 1}/{len(sequence)}" if current_idx >= 0 else "0/6",
            "human_feedback": state.get("human_feedback", ""),
            "error": state.get("error_message", ""),
            "updated_at": state.get("updated_at", datetime.utcnow().isoformat()),
        }
