"""
Agent 02: The Hook Writer (Hook Dept.)
Core Directive: Own the first two seconds.
Workflow: Draft (ten openings, fast) → Cut (keep what stops thumbs) → Hand off (winner goes to script)
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are The Hook Writer — Agent 02 of The Loop content creation system.

## CORE DIRECTIVE
Own the first two seconds. If the hook fails, nothing else matters.

## YOUR RULES
1. Write TEN opening options for every single idea — no exceptions
2. Lead with NUMERICAL PROOF — numbers beat promises every time
3. Kill generic/weak lines in the draft phase — be ruthless
4. Tune hooks to match the specific platform format:
   - Instagram Reels: Visual hook + text overlay (max 8 words)
   - TikTok: Pattern interrupt + curiosity gap (max 6 words spoken)
   - YouTube Shorts: Bold claim + immediate proof tease
   - X/Twitter: Contrarian take + thread hook
   - LinkedIn: Authority statement + insight preview

## HOOK FORMULAS THAT WORK
- "I [did X] in [time] — here's how" (proof-first)
- "[Number] [things] that [surprising result]" (list hook)
- "Stop [common action] — do this instead" (pattern interrupt)
- "The [number] rule of [topic] nobody talks about" (curiosity)
- "I asked [authority] [question] — their answer shocked me" (borrowed credibility)

## OUTPUT FORMAT
Return valid JSON:
{
    "hooks_by_idea": [
        {
            "idea_id": "the content idea ID this hooks to",
            "idea_title": "title of the idea",
            "hooks": [
                {
                    "id": "hook-unique-id",
                    "text": "The hook text",
                    "platform": "target platform",
                    "hook_type": "proof|list|interrupt|curiosity|credibility|contrarian",
                    "strength_score": 1-10,
                    "reasoning": "Why this hook works"
                }
            ],
            "winner": {
                "id": "id of the best hook",
                "text": "the winning hook text",
                "reasoning": "Why this is the winner"
            },
            "title_variants": ["Title option 1", "Title option 2", "Title option 3"],
            "thumbnail_text_options": ["Short punchy text 1", "Text 2", "Text 3"]
        }
    ]
}
"""


class HookWriterAgent:
    """Agent 02: The Hook Writer — crafts attention-grabbing openings."""

    def __init__(self):
        self.name = "hook_writer"
        self.display_name = "The Hook Writer"
        self.department = "Hook Dept."

    async def run(self, state: dict) -> dict:
        """
        Execute the hook writing pipeline.
        Draft 10 → Cut weak → Hand off winner
        """
        logger.info(f"[{self.display_name}] Starting hook writing for cycle #{state.get('cycle_number', 1)}")

        content_ideas = state.get("content_ideas", [])
        if not content_ideas:
            logger.warning(f"[{self.display_name}] No content ideas to write hooks for!")
            return {
                "hooks": [],
                "selected_hook": {},
                "current_agent": "hook_writer",
                "approval_status": "pending",
                "updated_at": datetime.utcnow().isoformat(),
            }

        # Generate hooks for each idea
        result = await self._generate_hooks(content_ideas, state)

        # Flatten all hooks into the hooks list
        all_hooks = []
        selected_hook = {}
        for idea_hooks in result.get("hooks_by_idea", []):
            for hook in idea_hooks.get("hooks", []):
                hook["idea_id"] = idea_hooks.get("idea_id", "")
                all_hooks.append(hook)
            if idea_hooks.get("winner") and not selected_hook:
                selected_hook = {
                    **idea_hooks["winner"],
                    "idea_id": idea_hooks.get("idea_id", ""),
                    "idea_title": idea_hooks.get("idea_title", ""),
                    "title_variants": idea_hooks.get("title_variants", []),
                    "thumbnail_text_options": idea_hooks.get("thumbnail_text_options", []),
                }

        return {
            "hooks": all_hooks,
            "selected_hook": selected_hook,
            "current_agent": "hook_writer",
            "approval_status": "pending",
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def _generate_hooks(self, content_ideas: list[dict], state: dict) -> dict:
        """Use LLM to generate 10 hooks per content idea."""
        # Take top ideas (max 5 to keep scope manageable)
        top_ideas = sorted(
            content_ideas,
            key=lambda x: x.get("urgency", "low") == "high",
            reverse=True,
        )[:5]

        trends = state.get("trends", [])
        viral_refs = state.get("viral_references", [])
        human_feedback = state.get("human_feedback", "")

        user_message = f"""Generate hooks for the following content ideas.

## Content Ideas
{json.dumps(top_ideas, indent=2, default=str)}

## Trend Context (for relevance)
{json.dumps(trends[:5], indent=2, default=str) if trends else "No trend data available."}

## Viral References (for inspiration)
{json.dumps(viral_refs[:3], indent=2, default=str) if viral_refs else "No viral references available."}

{f'## Human Feedback from Previous Round{chr(10)}{human_feedback}' if human_feedback else ''}

## Instructions
1. Write EXACTLY 10 hooks for each idea — no fewer
2. Score each hook honestly from 1-10
3. Kill any hook below a 6 — replace it with something better
4. Select ONE winner per idea — the one most likely to stop thumbs
5. Generate 3 title variants and 3 thumbnail text options per idea
6. Every hook MUST lead with numbers or proof where possible
7. Assign unique IDs (format: hook-XXXX)

Return ONLY valid JSON."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.9,  # Higher temp for creative variety
                max_tokens=6000,
            )

            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()

            result = json.loads(clean)

            # Ensure all hooks have IDs
            for idea_hooks in result.get("hooks_by_idea", []):
                for hook in idea_hooks.get("hooks", []):
                    if "id" not in hook:
                        hook["id"] = f"hook-{uuid.uuid4().hex[:8]}"

            total_hooks = sum(len(ih.get("hooks", [])) for ih in result.get("hooks_by_idea", []))
            logger.info(f"[{self.display_name}] Generated {total_hooks} hooks across {len(result.get('hooks_by_idea', []))} ideas")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[{self.display_name}] Failed to parse hooks JSON: {e}")
            return {"hooks_by_idea": []}
        except Exception as e:
            logger.error(f"[{self.display_name}] Hook generation failed: {e}")
            return {"hooks_by_idea": []}
