"""
Agent 08: The Sentinel (Quality Dept.)
Core Directive: Guard every gate. Trust nothing without proof.
Workflow: Intercept -> Evaluate -> Score -> Enforce

Inspired by Buzz's hash-chain audit trail (buzz-audit) and workflow
validation engine (buzz-workflow/schema.rs).  The Sentinel sits between
each agent output and approval gate, providing automated quality
scoring so human reviewers have data, not just vibes.
"""

import json
import logging
import uuid
import hashlib
from datetime import datetime
from typing import Any, Optional

from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = '''You are The Sentinel -- Agent 08 of the Noir content creation system.

## CORE DIRECTIVE
Guard every gate. Trust nothing without proof. You are the quality backbone.

## YOUR RESPONSIBILITIES
1. **Intercept**: Receive agent outputs before they reach the human approval gate
2. **Evaluate**: Score content quality, brand alignment, viral potential, and risk
3. **Score**: Assign a composite quality score (0-100) with breakdown
4. **Enforce**: Flag critical issues, auto-reject dangerous content, recommend improvements

## EVALUATION CRITERIA
- **Content Quality** (0-25): Writing quality, originality, depth of insight
- **Brand Alignment** (0-25): Consistency with brand voice, visual identity, values
- **Viral Potential** (0-25): Hook strength, shareability, emotional trigger, trend fit
- **Risk Assessment** (0-25): Legal safety, controversy level, platform compliance

## QUALITY THRESHOLDS
- 80-100: PASS -- Auto-recommend approval
- 60-79:  REVIEW -- Needs human attention (highlight concerns)
- 40-59:  CAUTION -- Significant issues detected (list all problems)
- 0-39:   BLOCK -- Critical quality failure (auto-reject with reasons)

## OUTPUT FORMAT
Return valid JSON:
{
    "quality_score": {
        "total": 0,
        "content_quality": 0,
        "brand_alignment": 0,
        "viral_potential": 0,
        "risk_assessment": 0
    },
    "verdict": "pass|review|caution|block",
    "flags": [
        {
            "severity": "critical|warning|info",
            "category": "category name",
            "message": "description of the issue",
            "suggestion": "how to fix it"
        }
    ],
    "improvements": [
        "Specific actionable improvement suggestion"
    ],
    "confidence": 0.0,
    "summary": "One-paragraph quality assessment"
}
'''

# ---------------------------------------------------------------------------
# Audit chain helpers (inspired by buzz-audit hash-chain)
# ---------------------------------------------------------------------------

def _compute_hash(data: str, prev_hash: str = "") -> str:
    """Compute a SHA-256 hash linking to the previous entry (hash-chain)."""
    payload = f"{prev_hash}|{data}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SentinelAgent:
    """Agent 08: The Sentinel -- quality gate enforcer and pipeline auditor."""

    def __init__(self):
        self.name = "sentinel"
        self.display_name = "The Sentinel"
        self.department = "Quality Dept."
        self._audit_chain: list[dict] = []

    async def run(self, state: dict) -> dict:
        """
        Execute the sentinel evaluation pipeline.
        Intercept -> Evaluate -> Score -> Enforce
        """
        current_agent = state.get("current_agent", "unknown")
        logger.info(
            f"[{self.display_name}] Evaluating output from '{current_agent}' "
            f"(cycle #{state.get('cycle_number', 1)})"
        )

        self._audit_chain = list(state.get("audit_trail", []))

        evaluation = await self._evaluate(current_agent, state)

        audit_entry = self._record_audit(current_agent, evaluation, state)

        now = datetime.utcnow().isoformat()
        return {
            "sentinel_scores": {current_agent: evaluation},
            "audit_trail": self._audit_chain,
            "current_agent": current_agent,
            "updated_at": now,
        }

    async def evaluate_agent_output(self, agent_name: str, state: dict) -> dict:
        """Standalone evaluation callable outside the pipeline."""
        return await self._evaluate(agent_name, state)

    async def _evaluate(self, agent_name: str, state: dict) -> dict:
        """Use LLM to evaluate agent output quality."""
        output_data = self._extract_agent_output(agent_name, state)

        user_message = f"""Evaluate the following content from the '{agent_name}' agent.

## Agent Output
{json.dumps(output_data, indent=2, default=str)}

## Pipeline Context
- Cycle: #{state.get('cycle_number', 1)}
- Previous feedback: {state.get('human_feedback', 'None')}
- Error state: {state.get('error_message', 'None')}

## Instructions
1. Score each of the 4 quality dimensions (0-25 each)
2. Calculate the total score (0-100)
3. Determine the verdict based on thresholds
4. Flag any issues with severity ratings
5. Provide specific, actionable improvement suggestions
6. Be honest and direct -- never inflate scores

Return ONLY valid JSON matching the required output format."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
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

            evaluation = json.loads(clean)

            if "quality_score" not in evaluation:
                evaluation["quality_score"] = {"total": 50}
            if "verdict" not in evaluation:
                total = evaluation["quality_score"].get("total", 50)
                if total >= 80:
                    evaluation["verdict"] = "pass"
                elif total >= 60:
                    evaluation["verdict"] = "review"
                elif total >= 40:
                    evaluation["verdict"] = "caution"
                else:
                    evaluation["verdict"] = "block"

            logger.info(
                f"[{self.display_name}] {agent_name} scored "
                f"{evaluation['quality_score'].get('total', '?')}/100 "
                f"-> {evaluation.get('verdict', '?').upper()}"
            )
            return evaluation

        except json.JSONDecodeError as e:
            logger.error(f"[{self.display_name}] Failed to parse evaluation: {e}")
            return self._fallback_evaluation(agent_name)
        except Exception as e:
            logger.error(f"[{self.display_name}] Evaluation failed: {e}")
            return self._fallback_evaluation(agent_name)

    def _extract_agent_output(self, agent_name: str, state: dict) -> dict:
        """Extract relevant output fields for a given agent."""
        field_map = {
            "researcher": ["trends", "content_ideas", "viral_references"],
            "hook_writer": ["hooks", "selected_hook"],
            "script_writer": ["script", "captions", "hashtags"],
            "designer": ["design_briefs", "design_assets"],
            "publisher": ["publish_schedule", "publish_results"],
            "analyst": ["analytics", "insights"],
        }
        fields = field_map.get(agent_name, [])
        return {f: state.get(f, None) for f in fields if state.get(f)}

    def _fallback_evaluation(self, agent_name: str) -> dict:
        """Return a neutral evaluation when LLM call fails."""
        return {
            "quality_score": {
                "total": 50,
                "content_quality": 12,
                "brand_alignment": 12,
                "viral_potential": 13,
                "risk_assessment": 13,
            },
            "verdict": "review",
            "flags": [
                {
                    "severity": "warning",
                    "category": "system",
                    "message": "Automated evaluation unavailable -- manual review required",
                    "suggestion": "Review output carefully before approving",
                }
            ],
            "improvements": [],
            "confidence": 0.0,
            "summary": f"Automated evaluation for {agent_name} could not be completed. Manual review required.",
        }

    def _record_audit(self, agent_name: str, evaluation: dict, state: dict) -> dict:
        """Record an audit entry in the hash-chain."""
        prev_hash = self._audit_chain[-1]["hash"] if self._audit_chain else ""

        entry_data = json.dumps(
            {
                "agent": agent_name,
                "cycle": state.get("cycle_number", 1),
                "score": evaluation.get("quality_score", {}).get("total", 0),
                "verdict": evaluation.get("verdict", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
            },
            sort_keys=True,
        )

        entry = {
            "id": f"audit-{uuid.uuid4().hex[:8]}",
            "agent": agent_name,
            "cycle": state.get("cycle_number", 1),
            "score": evaluation.get("quality_score", {}).get("total", 0),
            "verdict": evaluation.get("verdict", "unknown"),
            "flags_count": len(evaluation.get("flags", [])),
            "timestamp": datetime.utcnow().isoformat(),
            "hash": _compute_hash(entry_data, prev_hash),
            "prev_hash": prev_hash,
        }

        self._audit_chain.append(entry)
        logger.info(
            f"[{self.display_name}] Audit entry #{len(self._audit_chain)} "
            f"recorded (hash: {entry['hash'][:12]}...)"
        )
        return entry

    @staticmethod
    def verify_audit_chain(chain: list[dict]) -> bool:
        """Verify the integrity of an audit chain."""
        for i, entry in enumerate(chain):
            expected_prev = chain[i - 1]["hash"] if i > 0 else ""
            if entry.get("prev_hash", "") != expected_prev:
                return False
        return True
