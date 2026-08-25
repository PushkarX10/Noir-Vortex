"""
Agent 03: The Script Writer (Script Dept.)
Core Directive: Every word is planned.
Workflow: Idea → Outline → Write → Refine → Deliver
Structure: Hook (first 3s) → Value (core) → Proof (results) → CTA (the ask)
"""

import json
import logging
import uuid
from datetime import datetime

from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are The Script Writer — Agent 03 of The Loop content creation system.

## CORE DIRECTIVE
Every. Word. Is. Planned. No filler, no fluff, no wasted breath.

## SCRIPT STRUCTURE (The 4-Part Framework)
Every script MUST follow this structure:
1. **HOOK** (0-3 seconds): The winning hook from Agent 02. Grabs attention immediately.
2. **VALUE** (The Core): The main insight, tip, story, or lesson. This is WHY they keep watching.
3. **PROOF** (Results/Evidence): Show don't tell. Numbers, screenshots, testimonials, before/after.
4. **CTA** (The Ask): One clear next step. Follow, save, share, link in bio, comment.

## CONTENT TYPES YOU PRODUCE
- **Reels Scripts** (15-90s): Tight, punchy, visual cues in brackets [B-roll: typing on laptop]
- **Carousel Scripts** (5-10 slides): Each slide = one complete thought, visual + text
- **YouTube Scripts** (1-15 min): Full structure with timestamps and B-roll notes
- **Captions**: Platform-optimized captions with line breaks and emoji strategy
- **Hashtag Packs**: 20-30 researched hashtags per post, tiered by size (small/medium/large)

## WRITING RULES
- Write at an 8th-grade reading level — clarity beats cleverness
- Use short sentences. One idea per line.
- Include [VISUAL CUE] markers for the designer/editor
- Every script needs timing estimates per section
- Captions: Hook line first, then value, then CTA. Use line breaks.

## OUTPUT FORMAT
Return valid JSON:
{
    "scripts": [
        {
            "id": "script-unique-id",
            "idea_id": "connected content idea ID",
            "hook_id": "connected hook ID",
            "title": "Script title",
            "content_type": "reel|carousel|youtube|thread",
            "target_platform": "primary platform",
            "total_duration": "estimated duration in seconds or slides",
            "sections": {
                "hook": {
                    "text": "The opening hook text",
                    "duration": "0-3s",
                    "visual_cue": "[What viewer sees]"
                },
                "value": {
                    "text": "The core value/insight section",
                    "duration": "3-45s or slides 2-7",
                    "visual_cues": ["[Cue 1]", "[Cue 2]"],
                    "key_points": ["Point 1", "Point 2", "Point 3"]
                },
                "proof": {
                    "text": "The proof/results section",
                    "duration": "45-60s or slide 8",
                    "visual_cue": "[Evidence shown]"
                },
                "cta": {
                    "text": "The call-to-action",
                    "duration": "last 5s or final slide",
                    "action": "follow|save|share|comment|link"
                }
            },
            "full_script": "Complete script text with all visual cues inline"
        }
    ],
    "captions": [
        {
            "script_id": "linked script ID",
            "platform": "platform name",
            "caption_text": "Full caption with formatting",
            "cta_line": "The specific CTA in the caption"
        }
    ],
    "hashtag_packs": [
        {
            "script_id": "linked script ID",
            "platform": "platform name",
            "hashtags": {
                "small": ["#niche1", "#niche2"],
                "medium": ["#mid1", "#mid2"],
                "large": ["#broad1", "#broad2"]
            }
        }
    ]
}
"""


class ScriptWriterAgent:
    """Agent 03: The Script Writer — structures every word of every content piece."""

    def __init__(self):
        self.name = "script_writer"
        self.display_name = "The Script Writer"
        self.department = "Script Dept."

    async def run(self, state: dict) -> dict:
        """
        Execute the script writing pipeline.
        Idea → Outline → Write → Refine → Deliver
        """
        logger.info(f"[{self.display_name}] Starting script writing for cycle #{state.get('cycle_number', 1)}")

        selected_hook = state.get("selected_hook", {})
        content_ideas = state.get("content_ideas", [])
        hooks = state.get("hooks", [])

        if not selected_hook and not hooks:
            logger.warning(f"[{self.display_name}] No hooks available!")
            return {
                "script": {},
                "captions": [],
                "hashtags": [],
                "current_agent": "script_writer",
                "approval_status": "pending",
                "updated_at": datetime.utcnow().isoformat(),
            }

        result = await self._write_scripts(selected_hook, content_ideas, hooks, state)

        # Extract the primary script
        scripts = result.get("scripts", [])
        primary_script = scripts[0] if scripts else {}

        # Flatten captions and hashtags
        captions = [c.get("caption_text", "") for c in result.get("captions", []) if c.get("caption_text")]
        hashtag_packs = result.get("hashtag_packs", [])
        all_hashtags = []
        for pack in hashtag_packs:
            tags = pack.get("hashtags", {})
            for tier_tags in tags.values():
                all_hashtags.extend(tier_tags)

        return {
            "script": primary_script,
            "captions": captions,
            "hashtags": list(set(all_hashtags)),  # Deduplicate
            "current_agent": "script_writer",
            "approval_status": "pending",
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def _write_scripts(self, selected_hook: dict, content_ideas: list, hooks: list, state: dict) -> dict:
        """Use LLM to write full scripts based on hooks and ideas."""
        human_feedback = state.get("human_feedback", "")

        # Find the idea matching the selected hook
        target_idea = {}
        if selected_hook.get("idea_id"):
            for idea in content_ideas:
                if idea.get("id") == selected_hook["idea_id"]:
                    target_idea = idea
                    break

        user_message = f"""Write complete, production-ready scripts for the following content.

## Selected Winning Hook
{json.dumps(selected_hook, indent=2, default=str)}

## Target Content Idea
{json.dumps(target_idea, indent=2, default=str) if target_idea else "Use the hook to infer the content direction."}

## All Available Hooks (for alternative angles)
{json.dumps(hooks[:10], indent=2, default=str) if hooks else "Only the selected hook is available."}

{f'## Human Feedback{chr(10)}{human_feedback}' if human_feedback else ''}

## Instructions
1. Write at LEAST one complete script using the selected hook
2. If the idea suits multiple formats, write scripts for each (reel + carousel, etc.)
3. Follow the Hook → Value → Proof → CTA structure STRICTLY
4. Include [VISUAL CUE] markers throughout
5. Write platform-optimized captions for each script
6. Generate hashtag packs with small/medium/large tiers
7. Assign unique IDs (format: script-XXXX, caption-XXXX)
8. Make every word count — cut ruthlessly

Return ONLY valid JSON."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.7,
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

            # Ensure IDs
            for script in result.get("scripts", []):
                if "id" not in script:
                    script["id"] = f"script-{uuid.uuid4().hex[:8]}"

            logger.info(
                f"[{self.display_name}] Generated {len(result.get('scripts', []))} scripts, "
                f"{len(result.get('captions', []))} captions, "
                f"{len(result.get('hashtag_packs', []))} hashtag packs"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[{self.display_name}] Failed to parse scripts JSON: {e}")
            return {"scripts": [], "captions": [], "hashtag_packs": []}
        except Exception as e:
            logger.error(f"[{self.display_name}] Script writing failed: {e}")
            return {"scripts": [], "captions": [], "hashtag_packs": []}
