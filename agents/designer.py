"""
Agent 04: The Designer (Design Dept.)
Core Directive: Design every post.
Workflow: Brief → Concept → Design → Revise → Deliver
Brand: ink black, deep blue, accent cyan, SF Pro font
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from config import BrandConfig, AppConfig
from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are The Designer — Agent 04 of The Loop content creation system.

## CORE DIRECTIVE
Design every post. You are the visual architect — every pixel matters.

## BRAND SYSTEM
- **Primary**: Ink Black (#0A0A0F) — backgrounds, depth
- **Secondary**: Deep Blue (#1E3A5F) — accents, headers
- **Accent**: Electric Cyan (#00D4FF) — CTAs, highlights, emphasis
- **Text**: Light (#E8E8ED) on dark backgrounds
- **Font**: SF Pro Display (primary), Inter (fallback)

## DESIGN PRINCIPLES
1. **Contrast is king** — text must pop against backgrounds
2. **Negative space** — let designs breathe, don't overcrowd
3. **Visual hierarchy** — the eye should flow: headline → visual → CTA
4. **Brand consistency** — every piece should feel like it belongs to the same brand
5. **Platform-native** — designs should feel native to each platform's aesthetic

## CONTENT TYPES YOU DESIGN
- **Carousel Slides** (1080x1350): 5-10 slides, each a complete visual thought
- **Thumbnails** (1280x720 / 1080x1920): CTR-driving thumbnails with bold text
- **Reel Covers** (1080x1920): Clean, branded covers for saved content
- **Post Graphics** (1080x1080): Single-image posts with text overlay
- **Story Templates** (1080x1920): Interactive story layouts

## OUTPUT FORMAT
Return valid JSON with design briefs and specifications:
{
    "design_briefs": [
        {
            "id": "design-unique-id",
            "script_id": "connected script ID",
            "content_type": "carousel|thumbnail|reel_cover|post|story",
            "platform": "target platform",
            "dimensions": "WxH in pixels",
            "slides": [
                {
                    "slide_number": 1,
                    "headline": "Bold headline text",
                    "body_text": "Supporting text if any",
                    "visual_description": "Detailed description of the visual/image needed",
                    "text_placement": "center|top|bottom|left|right",
                    "background": "color/gradient/image description",
                    "accent_elements": ["element descriptions"]
                }
            ],
            "color_palette": ["#hex1", "#hex2", "#hex3"],
            "typography": {
                "headline_font": "font name",
                "headline_size": "approximate size",
                "body_font": "font name",
                "body_size": "approximate size"
            },
            "mood": "descriptive mood/feel",
            "ai_image_prompts": [
                "Detailed prompt for AI image generation for each needed visual"
            ]
        }
    ]
}
"""


class DesignerAgent:
    """Agent 04: The Designer — creates visual specifications and AI image prompts."""

    def __init__(self):
        self.name = "designer"
        self.display_name = "The Designer"
        self.department = "Design Dept."

    async def run(self, state: dict) -> dict:
        """
        Execute the design pipeline.
        Brief → Concept → Design → Revise → Deliver
        """
        logger.info(f"[{self.display_name}] Starting design for cycle #{state.get('cycle_number', 1)}")

        script = state.get("script", {})
        selected_hook = state.get("selected_hook", {})
        captions = state.get("captions", [])

        if not script:
            logger.warning(f"[{self.display_name}] No script to design for!")
            return {
                "design_briefs": [],
                "design_assets": [],
                "current_agent": "designer",
                "approval_status": "pending",
                "updated_at": datetime.utcnow().isoformat(),
            }

        result = await self._create_designs(script, selected_hook, captions, state)

        # Generate asset paths (where AI images would be saved)
        output_dir = Path(AppConfig.CONTENT_OUTPUT_DIR) / f"cycle-{state.get('cycle_number', 1)}"
        output_dir.mkdir(parents=True, exist_ok=True)

        asset_paths = []
        for brief in result.get("design_briefs", []):
            for i, slide in enumerate(brief.get("slides", [])):
                asset_path = str(output_dir / f"{brief['id']}_slide_{i + 1}.png")
                asset_paths.append(asset_path)

        return {
            "design_briefs": result.get("design_briefs", []),
            "design_assets": asset_paths,
            "current_agent": "designer",
            "approval_status": "pending",
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def _create_designs(self, script: dict, selected_hook: dict, captions: list, state: dict) -> dict:
        """Use LLM to create design briefs based on scripts."""
        human_feedback = state.get("human_feedback", "")
        brand = BrandConfig.to_dict()

        user_message = f"""Create detailed design briefs for the following content.

## Script to Design
{json.dumps(script, indent=2, default=str)}

## Winning Hook (for headline inspiration)
{json.dumps(selected_hook, indent=2, default=str)}

## Captions (for text content reference)
{json.dumps(captions[:3], indent=2, default=str) if captions else "No captions available."}

## Brand Kit
{json.dumps(brand, indent=2)}

{f'## Human Feedback{chr(10)}{human_feedback}' if human_feedback else ''}

## Instructions
1. Create design briefs for ALL relevant formats:
   - If it's a reel: thumbnail + reel cover
   - If it's a carousel: all slides (5-10)
   - If it's a post: main graphic + story template
2. Use the brand kit colors and fonts STRICTLY
3. Write DETAILED AI image prompts for each visual needed
4. Ensure text is readable — check contrast ratios mentally
5. Each slide should tell ONE clear visual story
6. Thumbnails MUST be click-worthy — bold, contrasting, curious
7. Assign unique IDs (format: design-XXXX)

Return ONLY valid JSON."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.8,
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

            for brief in result.get("design_briefs", []):
                if "id" not in brief:
                    brief["id"] = f"design-{uuid.uuid4().hex[:8]}"

            total_slides = sum(len(b.get("slides", [])) for b in result.get("design_briefs", []))
            logger.info(
                f"[{self.display_name}] Created {len(result.get('design_briefs', []))} briefs "
                f"with {total_slides} total slides/assets"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[{self.display_name}] Failed to parse design JSON: {e}")
            return {"design_briefs": []}
        except Exception as e:
            logger.error(f"[{self.display_name}] Design creation failed: {e}")
            return {"design_briefs": []}
