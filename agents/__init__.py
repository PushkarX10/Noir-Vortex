"""
Noir -- Agent Layer
All 10 AI agents that form the content creation pipeline.
Agents 01-07: Original pipeline agents
Agents 08-10: Buzz-integrated premium agents (Sentinel, Collaborator, Automator)
"""

from agents.state import PipelineState
from agents.researcher import ResearcherAgent
from agents.hook_writer import HookWriterAgent
from agents.script_writer import ScriptWriterAgent
from agents.designer import DesignerAgent
from agents.analyst import AnalystAgent
from agents.manager import ManagerAgent
from agents.publisher import PublisherAgent
from agents.sentinel import SentinelAgent
from agents.collaborator import CollaboratorAgent
from agents.automator import AutomatorAgent

__all__ = [
    "PipelineState",
    "ResearcherAgent",
    "HookWriterAgent",
    "ScriptWriterAgent",
    "DesignerAgent",
    "AnalystAgent",
    "ManagerAgent",
    "PublisherAgent",
    "SentinelAgent",
    "CollaboratorAgent",
    "AutomatorAgent",
]
