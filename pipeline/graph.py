"""
The Loop — LangGraph Pipeline Graph
The core state machine that orchestrates all 7 agents.
Uses interrupt_before at each approval gate for human-in-the-loop control.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import PipelineState, initial_state
from agents.researcher import ResearcherAgent
from agents.hook_writer import HookWriterAgent
from agents.script_writer import ScriptWriterAgent
from agents.designer import DesignerAgent
from agents.analyst import AnalystAgent
from agents.publisher import PublisherAgent
from agents.manager import ManagerAgent
from pipeline.approval import ApprovalGate

logger = logging.getLogger(__name__)

# Singleton agent instances
_researcher = ResearcherAgent()
_hook_writer = HookWriterAgent()
_script_writer = ScriptWriterAgent()
_designer = DesignerAgent()
_analyst = AnalystAgent()
_publisher = PublisherAgent()
_manager = ManagerAgent()


# ---------------------------------------------------------------------------
# Node functions (each wraps an agent's run method)
# ---------------------------------------------------------------------------

async def researcher_node(state: PipelineState) -> dict:
    """Node: Run the Researcher agent."""
    logger.info("═══ PIPELINE NODE: Researcher ═══")
    try:
        result = await _researcher.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Researcher node failed: {e}")
        return {
            "error_message": f"Researcher failed: {str(e)}",
            "current_agent": "researcher",
            "approval_status": "pending",
            "updated_at": datetime.utcnow().isoformat(),
        }


async def hook_writer_node(state: PipelineState) -> dict:
    """Node: Run the Hook Writer agent."""
    logger.info("═══ PIPELINE NODE: Hook Writer ═══")
    try:
        result = await _hook_writer.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Hook Writer node failed: {e}")
        return {
            "error_message": f"Hook Writer failed: {str(e)}",
            "current_agent": "hook_writer",
            "approval_status": "pending",
            "updated_at": datetime.utcnow().isoformat(),
        }


async def script_writer_node(state: PipelineState) -> dict:
    """Node: Run the Script Writer agent."""
    logger.info("═══ PIPELINE NODE: Script Writer ═══")
    try:
        result = await _script_writer.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Script Writer node failed: {e}")
        return {
            "error_message": f"Script Writer failed: {str(e)}",
            "current_agent": "script_writer",
            "approval_status": "pending",
            "updated_at": datetime.utcnow().isoformat(),
        }


async def designer_node(state: PipelineState) -> dict:
    """Node: Run the Designer agent."""
    logger.info("═══ PIPELINE NODE: Designer ═══")
    try:
        result = await _designer.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Designer node failed: {e}")
        return {
            "error_message": f"Designer failed: {str(e)}",
            "current_agent": "designer",
            "approval_status": "pending",
            "updated_at": datetime.utcnow().isoformat(),
        }


async def publisher_node(state: PipelineState) -> dict:
    """Node: Run the Publisher agent."""
    logger.info("═══ PIPELINE NODE: Publisher ═══")
    try:
        result = await _publisher.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Publisher node failed: {e}")
        return {
            "error_message": f"Publisher failed: {str(e)}",
            "current_agent": "publisher",
            "updated_at": datetime.utcnow().isoformat(),
        }


async def analyst_node(state: PipelineState) -> dict:
    """Node: Run the Analyst agent."""
    logger.info("═══ PIPELINE NODE: Analyst ═══")
    try:
        result = await _analyst.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Analyst node failed: {e}")
        return {
            "error_message": f"Analyst failed: {str(e)}",
            "current_agent": "analyst",
            "updated_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# Approval gate nodes (interrupt points)
# ---------------------------------------------------------------------------

async def approval_gate_research(state: PipelineState) -> dict:
    """Approval gate after Researcher. Pipeline pauses here for review."""
    logger.info("⏸  APPROVAL GATE: Research output awaiting review")
    return {
        "current_agent": "researcher",
        "approval_status": "pending",
        "updated_at": datetime.utcnow().isoformat(),
    }


async def approval_gate_hooks(state: PipelineState) -> dict:
    """Approval gate after Hook Writer."""
    logger.info("⏸  APPROVAL GATE: Hook output awaiting review")
    return {
        "current_agent": "hook_writer",
        "approval_status": "pending",
        "updated_at": datetime.utcnow().isoformat(),
    }


async def approval_gate_scripts(state: PipelineState) -> dict:
    """Approval gate after Script Writer."""
    logger.info("⏸  APPROVAL GATE: Script output awaiting review")
    return {
        "current_agent": "script_writer",
        "approval_status": "pending",
        "updated_at": datetime.utcnow().isoformat(),
    }


async def approval_gate_design(state: PipelineState) -> dict:
    """Approval gate after Designer."""
    logger.info("⏸  APPROVAL GATE: Design output awaiting review")
    return {
        "current_agent": "designer",
        "approval_status": "pending",
        "updated_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Routing functions (conditional edges)
# ---------------------------------------------------------------------------

def route_after_research_approval(state: PipelineState) -> str:
    """Route after research approval gate."""
    status = state.get("approval_status", "pending")
    if status == "approved":
        return "hook_writer"
    elif status in ("rejected", "revision_requested"):
        return "researcher"
    return END  # Pending — will be resumed via API


def route_after_hooks_approval(state: PipelineState) -> str:
    """Route after hooks approval gate."""
    status = state.get("approval_status", "pending")
    if status == "approved":
        return "script_writer"
    elif status in ("rejected", "revision_requested"):
        return "hook_writer"
    return END


def route_after_scripts_approval(state: PipelineState) -> str:
    """Route after scripts approval gate."""
    status = state.get("approval_status", "pending")
    if status == "approved":
        return "designer"
    elif status in ("rejected", "revision_requested"):
        return "script_writer"
    return END


def route_after_design_approval(state: PipelineState) -> str:
    """Route after design approval gate."""
    status = state.get("approval_status", "pending")
    if status == "approved":
        return "publisher"
    elif status in ("rejected", "revision_requested"):
        return "designer"
    return END


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_pipeline_graph() -> StateGraph:
    """
    Build the complete LangGraph state machine for The Loop pipeline.

    Flow:
        Researcher → [Approval] → Hook Writer → [Approval] →
        Script Writer → [Approval] → Designer → [Approval] →
        Publisher → Analyst → END

    Returns:
        Compiled StateGraph ready for execution.
    """
    builder = StateGraph(PipelineState)

    # Add agent nodes
    builder.add_node("researcher", researcher_node)
    builder.add_node("hook_writer", hook_writer_node)
    builder.add_node("script_writer", script_writer_node)
    builder.add_node("designer", designer_node)
    builder.add_node("publisher", publisher_node)
    builder.add_node("analyst", analyst_node)

    # Add approval gate nodes
    builder.add_node("approval_research", approval_gate_research)
    builder.add_node("approval_hooks", approval_gate_hooks)
    builder.add_node("approval_scripts", approval_gate_scripts)
    builder.add_node("approval_design", approval_gate_design)

    # Set entry point
    builder.set_entry_point("researcher")

    # Define edges: Agent → Approval Gate
    builder.add_edge("researcher", "approval_research")
    builder.add_edge("hook_writer", "approval_hooks")
    builder.add_edge("script_writer", "approval_scripts")
    builder.add_edge("designer", "approval_design")

    # Conditional edges: Approval Gate → Next Agent or Retry
    builder.add_conditional_edges(
        "approval_research",
        route_after_research_approval,
        {"hook_writer": "hook_writer", "researcher": "researcher", END: END},
    )
    builder.add_conditional_edges(
        "approval_hooks",
        route_after_hooks_approval,
        {"script_writer": "script_writer", "hook_writer": "hook_writer", END: END},
    )
    builder.add_conditional_edges(
        "approval_scripts",
        route_after_scripts_approval,
        {"designer": "designer", "script_writer": "script_writer", END: END},
    )
    builder.add_conditional_edges(
        "approval_design",
        route_after_design_approval,
        {"publisher": "publisher", "designer": "designer", END: END},
    )

    # Publisher → Analyst → END (no approval needed for these)
    builder.add_edge("publisher", "analyst")
    builder.add_edge("analyst", END)

    return builder


async def create_compiled_graph(db_path: str = "./data/theloop.db"):
    """
    Create and compile the pipeline graph with a checkpointer.

    Returns:
        Tuple of (compiled_graph, checkpointer)
    """
    checkpointer = MemorySaver()

    # Build and compile
    builder = build_pipeline_graph()
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=[
            "approval_research",
            "approval_hooks",
            "approval_scripts",
            "approval_design",
        ],
    )

    logger.info("[Pipeline] Graph compiled with 4 approval gates")
    return graph, checkpointer


def get_manager() -> ManagerAgent:
    """Get the Manager agent instance."""
    return _manager
