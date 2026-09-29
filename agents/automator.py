"""
Agent 10: The Automator (Workflow Dept.)
Core Directive: Automate everything that can be automated.
Workflow: Define -> Trigger -> Execute -> Report

Inspired by Buzz's YAML-as-code workflow engine (buzz-workflow/schema.rs,
executor.rs).  The Automator brings programmable workflow definitions to
Noir -- scheduled pipeline runs, webhook triggers, conditional step
execution, and timeout management.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = '''You are The Automator -- Agent 10 of the Noir content creation system.

## CORE DIRECTIVE
Automate everything that can be automated. Humans should decide, not babysit.

## YOUR RESPONSIBILITIES
1. **Define**: Create and manage workflow definitions (YAML-style configs)
2. **Trigger**: Handle scheduled, webhook, and event-based pipeline triggers
3. **Execute**: Run automated steps (posting, notifications, data collection)
4. **Report**: Summarize automation results and suggest optimizations

## YOUR CAPABILITIES
- Generate workflow definitions for recurring content pipelines
- Optimize posting schedules based on analytics data
- Auto-trigger pipeline runs on schedules (daily, weekly, custom cron)
- Webhook integration for external service triggers
- Conditional workflow routing based on sentinel scores
- Timeout and retry management for each pipeline step

## WORKFLOW DEFINITION FORMAT (inspired by Buzz workflows)
A workflow has:
- name: Human-readable name
- trigger: What starts the workflow (schedule, webhook, manual)
- steps: Ordered list of actions with conditions
- enabled: Whether the workflow is active

## OUTPUT FORMAT
Return valid JSON:
{
    "workflows": [
        {
            "id": "unique-id",
            "name": "Workflow name",
            "description": "What this workflow does",
            "trigger": {
                "type": "schedule|webhook|manual|event",
                "config": {
                    "cron": "0 9 * * 1",
                    "timezone": "UTC"
                }
            },
            "steps": [
                {
                    "id": "step-id",
                    "name": "Step name",
                    "action": "run_pipeline|post_content|send_notification|call_webhook|delay",
                    "config": {},
                    "condition": "optional condition expression",
                    "timeout_secs": 300
                }
            ],
            "enabled": true
        }
    ],
    "schedule_recommendations": [
        {
            "platform": "platform name",
            "best_times": ["HH:MM UTC"],
            "best_days": ["Monday", "Wednesday"],
            "reasoning": "Why these times"
        }
    ],
    "automation_insights": [
        "Actionable insight about workflow optimization"
    ]
}
'''


# ---------------------------------------------------------------------------
# Workflow Definition Types (Python port of Buzz schema.rs)
# ---------------------------------------------------------------------------

class TriggerDef:
    """Workflow trigger definition (mirrors Buzz TriggerDef)."""

    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    MANUAL = "manual"
    EVENT = "event"

    def __init__(self, trigger_type: str, config: dict = None):
        self.type = trigger_type
        self.config = config or {}

    def to_dict(self) -> dict:
        return {"type": self.type, "config": self.config}

    @classmethod
    def from_dict(cls, data: dict) -> "TriggerDef":
        return cls(data.get("type", "manual"), data.get("config", {}))


class StepDef:
    """Workflow step definition (mirrors Buzz Step)."""

    def __init__(
        self,
        step_id: str,
        name: str,
        action: str,
        config: dict = None,
        condition: str = None,
        timeout_secs: int = 300,
    ):
        self.id = step_id
        self.name = name
        self.action = action
        self.config = config or {}
        self.condition = condition
        self.timeout_secs = timeout_secs

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "action": self.action,
            "config": self.config,
            "timeout_secs": self.timeout_secs,
        }
        if self.condition:
            d["condition"] = self.condition
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "StepDef":
        return cls(
            step_id=data.get("id", f"step-{uuid.uuid4().hex[:6]}"),
            name=data.get("name", "Unnamed Step"),
            action=data.get("action", "run_pipeline"),
            config=data.get("config", {}),
            condition=data.get("condition"),
            timeout_secs=data.get("timeout_secs", 300),
        )


class WorkflowDef:
    """
    Top-level workflow definition (mirrors Buzz WorkflowDef from schema.rs).
    Authored in JSON, can be extended to YAML parsing.
    """

    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str = "",
        trigger: TriggerDef = None,
        steps: list[StepDef] = None,
        enabled: bool = True,
    ):
        self.id = workflow_id
        self.name = name
        self.description = description
        self.trigger = trigger or TriggerDef("manual")
        self.steps = steps or []
        self.enabled = enabled
        self.created_at = datetime.utcnow().isoformat()

    def validate(self) -> tuple[bool, str]:
        """Validate the workflow definition (mirrors Buzz WorkflowDef::validate)."""
        if not self.name.strip():
            return False, "name is required and must not be empty"
        if not self.steps:
            return False, "at least one step is required"
        seen_ids = set()
        for step in self.steps:
            if not step.id.strip():
                return False, "step id must not be empty"
            if step.id in seen_ids:
                return False, f"duplicate step id: {step.id}"
            seen_ids.add(step.id)
        return True, "valid"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "enabled": self.enabled,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowDef":
        return cls(
            workflow_id=data.get("id", f"wf-{uuid.uuid4().hex[:8]}"),
            name=data.get("name", "Unnamed Workflow"),
            description=data.get("description", ""),
            trigger=TriggerDef.from_dict(data.get("trigger", {})),
            steps=[StepDef.from_dict(s) for s in data.get("steps", [])],
            enabled=data.get("enabled", True),
        )


class AutomatorAgent:
    """Agent 10: The Automator -- workflow automation and scheduling."""

    def __init__(self):
        self.name = "automator"
        self.display_name = "The Automator"
        self.department = "Workflow Dept."
        self.workflows: list[WorkflowDef] = []

    async def run(self, state: dict) -> dict:
        """
        Execute the automator pipeline.
        Define -> Trigger -> Execute -> Report
        """
        logger.info(
            f"[{self.display_name}] Generating workflow recommendations "
            f"(cycle #{state.get('cycle_number', 1)})"
        )

        # Load existing workflows from state
        existing_wfs = state.get("workflow_definitions", [])
        self.workflows = [WorkflowDef.from_dict(w) for w in existing_wfs]

        # Generate optimized workflow recommendations
        recommendations = await self._generate_recommendations(state)

        # Build default workflows if none exist
        if not self.workflows:
            self.workflows = self._build_default_workflows(state)

        now = datetime.utcnow().isoformat()
        return {
            "workflow_definitions": [w.to_dict() for w in self.workflows],
            "schedule_recommendations": recommendations.get("schedule_recommendations", []),
            "automation_insights": recommendations.get("automation_insights", []),
            "current_agent": "automator",
            "updated_at": now,
        }

    def _build_default_workflows(self, state: dict) -> list[WorkflowDef]:
        """Create default workflows for common content pipeline patterns."""
        workflows = []

        # 1. Weekly Content Pipeline
        weekly = WorkflowDef(
            workflow_id=f"wf-{uuid.uuid4().hex[:8]}",
            name="Weekly Content Pipeline",
            description="Run the full content pipeline every Monday at 9am UTC",
            trigger=TriggerDef("schedule", {"cron": "0 9 * * 1", "timezone": "UTC"}),
            steps=[
                StepDef("run_pipeline", "Run Full Pipeline", "run_pipeline", {"mode": "full"}),
                StepDef("notify_team", "Notify Team", "send_notification", {
                    "message": "Weekly content pipeline completed",
                    "channels": ["dashboard"],
                }),
            ],
        )
        workflows.append(weekly)

        # 2. Daily Trend Check
        daily_trends = WorkflowDef(
            workflow_id=f"wf-{uuid.uuid4().hex[:8]}",
            name="Daily Trend Scanner",
            description="Run the researcher agent daily at 8am to catch emerging trends",
            trigger=TriggerDef("schedule", {"cron": "0 8 * * *", "timezone": "UTC"}),
            steps=[
                StepDef("scan_trends", "Scan Trends", "run_pipeline", {"mode": "research_only"}),
                StepDef(
                    "alert_high_virality",
                    "Alert on High Virality",
                    "send_notification",
                    {"message": "High virality trend detected"},
                    condition="sentinel_score > 80",
                ),
            ],
        )
        workflows.append(daily_trends)

        # 3. Auto-Publish Approved Content
        auto_publish = WorkflowDef(
            workflow_id=f"wf-{uuid.uuid4().hex[:8]}",
            name="Auto-Publish Approved",
            description="Automatically publish content that passes all approval gates with high sentinel scores",
            trigger=TriggerDef("event", {"event": "all_gates_approved"}),
            steps=[
                StepDef(
                    "check_quality",
                    "Verify Quality Score",
                    "run_pipeline",
                    {"mode": "sentinel_check"},
                    condition="sentinel_score >= 85",
                ),
                StepDef("publish", "Publish Content", "post_content", {}),
                StepDef("notify_published", "Notify Published", "send_notification", {
                    "message": "Content auto-published successfully",
                }),
            ],
        )
        workflows.append(auto_publish)

        return workflows

    async def _generate_recommendations(self, state: dict) -> dict:
        """Use LLM to generate workflow and schedule recommendations."""
        analytics = state.get("analytics", {})
        insights = state.get("insights", [])
        publish_results = state.get("publish_results", [])

        user_message = f"""Analyze the pipeline data and generate workflow automation recommendations.

## Analytics Data
{json.dumps(analytics, indent=2, default=str) if analytics else "No analytics data yet."}

## Previous Insights
{json.dumps(insights, indent=2) if insights else "No previous insights."}

## Published Content Results
{json.dumps(publish_results, indent=2, default=str) if publish_results else "No published content yet."}

## Instructions
1. Recommend optimal posting schedules per platform
2. Suggest workflow automations that would save time
3. Identify patterns that could be automated
4. Consider timezone, audience behavior, and platform algorithms
5. Be specific -- "post at 2pm EST on Tuesdays" not "post regularly"

Return ONLY valid JSON matching the required output format."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.6,
                max_tokens=2048,
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

            logger.info(
                f"[{self.display_name}] Generated "
                f"{len(report.get('schedule_recommendations', []))} schedule recommendations, "
                f"{len(report.get('automation_insights', []))} automation insights"
            )
            return report

        except json.JSONDecodeError as e:
            logger.error(f"[{self.display_name}] Failed to parse recommendations: {e}")
            return {"schedule_recommendations": [], "automation_insights": []}
        except Exception as e:
            logger.error(f"[{self.display_name}] Recommendation generation failed: {e}")
            return {"schedule_recommendations": [], "automation_insights": []}

    def add_workflow(self, workflow_dict: dict) -> tuple[bool, str]:
        """Add a new workflow definition after validation."""
        wf = WorkflowDef.from_dict(workflow_dict)
        valid, message = wf.validate()
        if not valid:
            return False, message
        self.workflows.append(wf)
        logger.info(f"[{self.display_name}] Workflow '{wf.name}' added (id: {wf.id})")
        return True, wf.id

    def remove_workflow(self, workflow_id: str) -> bool:
        """Remove a workflow by ID."""
        before = len(self.workflows)
        self.workflows = [w for w in self.workflows if w.id != workflow_id]
        removed = len(self.workflows) < before
        if removed:
            logger.info(f"[{self.display_name}] Workflow '{workflow_id}' removed")
        return removed

    def get_workflow(self, workflow_id: str) -> Optional[dict]:
        """Get a workflow definition by ID."""
        for w in self.workflows:
            if w.id == workflow_id:
                return w.to_dict()
        return None
