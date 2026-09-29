"""
Agent 09: The Collaborator (Orchestration Dept.)
Core Directive: No agent works alone. Context is everything.
Workflow: Observe -> Connect -> Share -> Handoff

Inspired by Buzz's agent communication protocol (buzz-acp), session
pooling (pool.rs), and agent handoff system (handoff.rs).  The
Collaborator manages inter-agent context sharing, enables agents to
request help from other agents mid-pipeline, and maintains persistent
memory across pipeline cycles.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = '''You are The Collaborator -- Agent 09 of the Noir content creation system.

## CORE DIRECTIVE
No agent works alone. Context is everything. You are the connective tissue.

## YOUR RESPONSIBILITIES
1. **Observe**: Track what each agent produces and what context they need
2. **Connect**: Identify when one agent's output can help another
3. **Share**: Synthesize cross-agent context into digestible briefs
4. **Handoff**: Manage smooth transitions between pipeline stages

## YOUR CAPABILITIES
- Synthesize context from all previous pipeline stages
- Generate "context briefs" that help downstream agents make better decisions
- Track patterns across multiple pipeline cycles (learning memory)
- Identify conflicting outputs between agents and resolve them
- Suggest when an agent should re-run with different parameters

## CONTEXT BRIEF FORMAT
For each downstream agent, create a focused brief:
- What the upstream agents discovered (key insights only)
- What worked in previous cycles (if any)
- What the human reviewer flagged (feedback history)
- Specific recommendations for the next agent

## OUTPUT FORMAT
Return valid JSON:
{
    "context_briefs": {
        "hook_writer": "Brief for the hook writer based on research",
        "script_writer": "Brief for the script writer based on hooks",
        "designer": "Brief for the designer based on scripts",
        "publisher": "Brief for the publisher based on designs"
    },
    "cross_agent_insights": [
        {
            "id": "unique-id",
            "source_agent": "agent that produced the insight",
            "target_agents": ["agents that should know"],
            "insight": "The actual cross-agent insight",
            "priority": "high|medium|low"
        }
    ],
    "cycle_memory": {
        "what_worked": ["things that performed well"],
        "what_failed": ["things that underperformed"],
        "patterns": ["recurring patterns across cycles"],
        "recommendations": ["strategic recommendations"]
    },
    "conflicts": [
        {
            "between": ["agent_a", "agent_b"],
            "issue": "Description of the conflict",
            "resolution": "Suggested resolution"
        }
    ]
}
'''


class CollaboratorAgent:
    """Agent 09: The Collaborator -- multi-agent orchestration and context sharing."""

    def __init__(self):
        self.name = "collaborator"
        self.display_name = "The Collaborator"
        self.department = "Orchestration Dept."

    async def run(self, state: dict) -> dict:
        """
        Execute the collaborator pipeline.
        Observe -> Connect -> Share -> Handoff
        """
        logger.info(
            f"[{self.display_name}] Building cross-agent context "
            f"(cycle #{state.get('cycle_number', 1)})"
        )

        # Build a comprehensive context synthesis
        context_report = await self._synthesize_context(state)

        now = datetime.utcnow().isoformat()
        return {
            "context_briefs": context_report.get("context_briefs", {}),
            "cross_agent_insights": context_report.get("cross_agent_insights", []),
            "cycle_memory": context_report.get("cycle_memory", {}),
            "current_agent": "collaborator",
            "updated_at": now,
        }

    async def generate_brief_for(self, target_agent: str, state: dict) -> str:
        """Generate a focused context brief for a specific downstream agent."""
        context_report = await self._synthesize_context(state)
        briefs = context_report.get("context_briefs", {})
        return briefs.get(target_agent, "No context brief available.")

    async def _synthesize_context(self, state: dict) -> dict:
        """Use LLM to synthesize cross-agent context."""
        pipeline_snapshot = {
            "cycle_number": state.get("cycle_number", 1),
            "current_agent": state.get("current_agent", "unknown"),
            "trends_count": len(state.get("trends", [])),
            "ideas_count": len(state.get("content_ideas", [])),
            "hooks_count": len(state.get("hooks", [])),
            "has_script": bool(state.get("script")),
            "designs_count": len(state.get("design_assets", [])),
            "published_count": len(state.get("publish_results", [])),
            "has_analytics": bool(state.get("analytics")),
            "human_feedback": state.get("human_feedback", ""),
            "sentinel_scores": state.get("sentinel_scores", {}),
            "previous_cycle_memory": state.get("cycle_memory", {}),
        }

        # Include summaries of key outputs (not full data to save tokens)
        key_outputs = {}
        if state.get("trends"):
            key_outputs["top_trends"] = [
                {"title": t.get("title", ""), "virality_score": t.get("virality_score", 0)}
                for t in state.get("trends", [])[:5]
            ]
        if state.get("content_ideas"):
            key_outputs["top_ideas"] = [
                {"title": i.get("title", ""), "urgency": i.get("urgency", "")}
                for i in state.get("content_ideas", [])[:5]
            ]
        if state.get("hooks"):
            key_outputs["hooks_summary"] = [
                {"text": h.get("text", "")[:100]} for h in state.get("hooks", [])[:3]
            ]
        if state.get("selected_hook"):
            key_outputs["selected_hook"] = state.get("selected_hook", {}).get("text", "")[:200]
        if state.get("script"):
            key_outputs["script_title"] = state.get("script", {}).get("title", "")
        if state.get("insights"):
            key_outputs["previous_insights"] = state.get("insights", [])[:5]

        user_message = f"""Synthesize cross-agent context for the Noir content pipeline.

## Pipeline Snapshot
{json.dumps(pipeline_snapshot, indent=2, default=str)}

## Key Agent Outputs
{json.dumps(key_outputs, indent=2, default=str)}

## Instructions
1. Create focused context briefs for each downstream agent
2. Identify cross-agent insights (what one agent found that helps another)
3. Build cycle memory (what worked, what failed, patterns, recommendations)
4. Flag any conflicts between agent outputs
5. Be concise -- agents have limited context windows

Return ONLY valid JSON matching the required output format."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=3072,
            )

            clean = response.strip()
            if clean.startswith("`"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("`"):
                    clean = clean[:-3]
                clean = clean.strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()

            report = json.loads(clean)

            # Ensure IDs on cross-agent insights
            for insight in report.get("cross_agent_insights", []):
                if "id" not in insight:
                    insight["id"] = f"insight-{uuid.uuid4().hex[:8]}"

            logger.info(
                f"[{self.display_name}] Context synthesized: "
                f"{len(report.get('context_briefs', {}))} briefs, "
                f"{len(report.get('cross_agent_insights', []))} insights"
            )
            return report

        except json.JSONDecodeError as e:
            logger.error(f"[{self.display_name}] Failed to parse context report: {e}")
            return self._fallback_context()
        except Exception as e:
            logger.error(f"[{self.display_name}] Context synthesis failed: {e}")
            return self._fallback_context()

    def _fallback_context(self) -> dict:
        """Return minimal context when LLM call fails."""
        return {
            "context_briefs": {},
            "cross_agent_insights": [],
            "cycle_memory": {
                "what_worked": [],
                "what_failed": [],
                "patterns": [],
                "recommendations": ["Context synthesis unavailable -- proceed with available data"],
            },
            "conflicts": [],
        }
