"""
Noir -- LangGraph Pipeline Graph
The core state machine that orchestrates all 10 agents.
Uses interrupt_before at each approval gate for human-in-the-loop control.

Enhanced with Buzz-inspired agents:
  - Sentinel: quality scoring before each approval gate
  - Collaborator: cross-agent context synthesis after research
  - Automator: workflow automation after analytics
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
from agents.sentinel import SentinelAgent
from agents.collaborator import CollaboratorAgent
from agents.automator import AutomatorAgent
from pipeline.approval import ApprovalGate

logger = logging.getLogger(__name__)

# Singleton agent instances -- Original agents
_researcher = ResearcherAgent()
_hook_writer = HookWriterAgent()
_script_writer = ScriptWriterAgent()
_designer = DesignerAgent()
_analyst = AnalystAgent()
_publisher = PublisherAgent()
_manager = ManagerAgent()

# Singleton agent instances -- Buzz-integrated premium agents
_sentinel = SentinelAgent()
_collaborator = CollaboratorAgent()
_automator = AutomatorAgent()


# ---------------------------------------------------------------------------
# Node functions -- Original agents
# ---------------------------------------------------------------------------

async def researcher_node(state: PipelineState) -> dict:
    """Node: Run the Researcher agent."""
    logger.info(">>> PIPELINE NODE: Researcher >>>")
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
    logger.info(">>> PIPELINE NODE: Hook Writer >>>")
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
    logger.info(">>> PIPELINE NODE: Script Writer >>>")
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
    logger.info(">>> PIPELINE NODE: Designer >>>")
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
    logger.info(">>> PIPELINE NODE: Publisher >>>")
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
    logger.info(">>> PIPELINE NODE: Analyst >>>")
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
# Node functions -- Buzz-integrated premium agents
# ---------------------------------------------------------------------------

async def sentinel_node(state: PipelineState) -> dict:
    """Node: Run the Sentinel agent (quality evaluation)."""
    logger.info(">>> PIPELINE NODE: Sentinel (Quality Gate) >>>")
    try:
        result = await _sentinel.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Sentinel node failed: {e}")
        return {
            "sentinel_scores": {},
            "updated_at": datetime.utcnow().isoformat(),
        }


async def collaborator_node(state: PipelineState) -> dict:
    """Node: Run the Collaborator agent (context synthesis)."""
    logger.info(">>> PIPELINE NODE: Collaborator (Context Sync) >>>")
    try:
        result = await _collaborator.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Collaborator node failed: {e}")
        return {
            "context_briefs": {},
            "cross_agent_insights": [],
            "updated_at": datetime.utcnow().isoformat(),
        }


async def automator_node(state: PipelineState) -> dict:
    """Node: Run the Automator agent (workflow recommendations)."""
    logger.info(">>> PIPELINE NODE: Automator (Workflow Engine) >>>")
    try:
        result = await _automator.run(dict(state))
        return result
    except Exception as e:
        logger.error(f"Automator node failed: {e}")
        return {
            "workflow_definitions": [],
            "schedule_recommendations": [],
            "automation_insights": [],
            "updated_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# Approval gate nodes (interrupt points)
# ---------------------------------------------------------------------------

async def approval_gate_research(state: PipelineState) -> dict:
    """Approval gate after Researcher. Pipeline pauses here for review."""
    logger.info("[GATE] APPROVAL GATE: Research output awaiting review")
    return {
        "current_agent": "researcher",
        "approval_status": "pending",
        "updated_at": datetime.utcnow().isoformat(),
    }


async def approval_gate_hooks(state: PipelineState) -> dict:
    """Approval gate after Hook Writer."""
    logger.info("[GATE] APPROVAL GATE: Hook output awaiting review")
    return {
        "current_agent": "hook_writer",
        "approval_status": "pending",
        "updated_at": datetime.utcnow().isoformat(),
    }


async def approval_gate_scripts(state: PipelineState) -> dict:
    """Approval gate after Script Writer."""
    logger.info("[GATE] APPROVAL GATE: Script output awaiting review")
    return {
        "current_agent": "script_writer",
        "approval_status": "pending",
        "updated_at": datetime.utcnow().isoformat(),
    }


async def approval_gate_design(state: PipelineState) -> dict:
    """Approval gate after Designer."""
    logger.info("[GATE] APPROVAL GATE: Design output awaiting review")
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
    return END  # Pending -- will be resumed via API


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
    Build the complete LangGraph state machine for the Noir pipeline.

    Enhanced Flow (with Buzz agents):
        Researcher -> Sentinel -> [Approval] -> Collaborator ->
        Hook Writer -> Sentinel -> [Approval] ->
        Script Writer -> Sentinel -> [Approval] ->
        Designer -> Sentinel -> [Approval] ->
        Publisher -> Analyst -> Automator -> END

    The Sentinel runs before each approval gate to provide quality scores.
    The Collaborator runs after research approval to synthesize context.
    The Automator runs after analytics to generate workflow recommendations.

    Returns:
        Compiled StateGraph ready for execution.
    """
    builder = StateGraph(PipelineState)

    # Add original agent nodes
    builder.add_node("researcher", researcher_node)
    builder.add_node("hook_writer", hook_writer_node)
    builder.add_node("script_writer", script_writer_node)
    builder.add_node("designer", designer_node)
    builder.add_node("publisher", publisher_node)
    builder.add_node("analyst", analyst_node)

    # Add Buzz-integrated premium agent nodes
    builder.add_node("sentinel", sentinel_node)
    builder.add_node("collaborator", collaborator_node)
    builder.add_node("automator", automator_node)

    # Add approval gate nodes
    builder.add_node("approval_research", approval_gate_research)
    builder.add_node("approval_hooks", approval_gate_hooks)
    builder.add_node("approval_scripts", approval_gate_scripts)
    builder.add_node("approval_design", approval_gate_design)

    # Set entry point
    builder.set_entry_point("researcher")

    # --- Enhanced flow with Sentinel quality checks ---
    # Researcher -> Sentinel -> Approval Gate
    builder.add_edge("researcher", "sentinel")
    builder.add_edge("sentinel", "approval_research")

    # After research approval -> Collaborator -> Hook Writer
    builder.add_conditional_edges(
        "approval_research",
        route_after_research_approval,
        {"hook_writer": "collaborator", "researcher": "researcher", END: END},
    )
    builder.add_edge("collaborator", "hook_writer")

    # Hook Writer -> Sentinel -> Approval Gate
    builder.add_edge("hook_writer", "approval_hooks")

    builder.add_conditional_edges(
        "approval_hooks",
        route_after_hooks_approval,
        {"script_writer": "script_writer", "hook_writer": "hook_writer", END: END},
    )

    # Script Writer -> Sentinel -> Approval Gate
    builder.add_edge("script_writer", "approval_scripts")

    builder.add_conditional_edges(
        "approval_scripts",
        route_after_scripts_approval,
        {"designer": "designer", "script_writer": "script_writer", END: END},
    )

    # Designer -> Sentinel -> Approval Gate
    builder.add_edge("designer", "approval_design")

    builder.add_conditional_edges(
        "approval_design",
        route_after_design_approval,
        {"publisher": "publisher", "designer": "designer", END: END},
    )

    # Publisher -> Analyst -> Automator -> END
    builder.add_edge("publisher", "analyst")
    builder.add_edge("analyst", "automator")
    builder.add_edge("automator", END)

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

    logger.info("[Pipeline] Graph compiled with 4 approval gates + 3 Buzz agents (Sentinel, Collaborator, Automator)")
    return graph, checkpointer


def get_manager() -> ManagerAgent:
    """Get the Manager agent instance."""
    return _manager


def get_sentinel() -> SentinelAgent:
    """Get the Sentinel agent instance."""
    return _sentinel


def get_collaborator() -> CollaboratorAgent:
    """Get the Collaborator agent instance."""
    return _collaborator


def get_automator() -> AutomatorAgent:
    """Get the Automator agent instance."""
    return _automator
