"""
Agent 07: The Publisher (Publishing)
Core Directive: Post on time, every time.
Workflow: Plan → Schedule → Publish → Confirm → Report
"""

import json
import logging
import uuid
from datetime import datetime

from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are The Publisher — Agent 07 of The Loop content creation system.

## CORE DIRECTIVE
Post on time, every time. Zero manual misses. Consistent delivery without losing momentum.

## YOUR RESPONSIBILITIES
1. **Plan**: Determine optimal posting times based on platform + audience data
2. **Schedule**: Queue content with precise timing across all platforms
3. **Publish**: Execute posts with correct assets, captions, hashtags per platform
4. **Confirm**: Verify each post is live and accessible
5. **Report**: Log post IDs, URLs, timestamps, and initial metrics

## PLATFORM-SPECIFIC RULES
- **Instagram**: Reels at peak hours (6-9 AM, 12-2 PM, 7-9 PM EST), include all hashtags in first comment
- **TikTok**: Post when target demo is active (varies), trending sounds boost discovery
- **YouTube Shorts**: Consistent daily posting wins, titles matter for search
- **X/Twitter**: Thread hooks in the morning, single posts in the evening
- **LinkedIn**: Weekday mornings (7-9 AM), professional tone, no hashtag spam

## OUTPUT FORMAT
Return valid JSON:
{
    "publish_plan": {
        "content_title": "What's being published",
        "platforms": [
            {
                "platform": "platform name",
                "scheduled_time": "ISO timestamp",
                "content_type": "reel|carousel|short|tweet|post",
                "caption": "Platform-optimized caption",
                "hashtags": ["platform-specific hashtags"],
                "assets": ["asset file references"],
                "special_notes": "Platform-specific instructions"
            }
        ]
    },
    "publish_results": [
        {
            "id": "result-unique-id",
            "platform": "platform name",
            "post_id": "platform-assigned post ID",
            "post_url": "direct URL to the post",
            "status": "published|scheduled|failed|draft",
            "published_at": "ISO timestamp",
            "error": "error message if failed, null otherwise"
        }
    ]
}
"""


class PublisherAgent:
    """Agent 07: The Publisher — handles cross-platform content publishing."""

    def __init__(self):
        self.name = "publisher"
        self.display_name = "The Publisher"
        self.department = "Publishing"

    async def run(self, state: dict) -> dict:
        """
        Execute the publishing pipeline.
        Plan → Schedule → Publish → Confirm → Report
        """
        logger.info(f"[{self.display_name}] Starting publishing for cycle #{state.get('cycle_number', 1)}")

        script = state.get("script", {})
        captions = state.get("captions", [])
        hashtags = state.get("hashtags", [])
        design_assets = state.get("design_assets", [])
        design_briefs = state.get("design_briefs", [])

        if not script:
            logger.warning(f"[{self.display_name}] No script to publish!")
            return {
                "publish_schedule": {},
                "publish_results": [],
                "current_agent": "publisher",
                "updated_at": datetime.utcnow().isoformat(),
            }

        # Plan the publication
        plan = await self._create_publish_plan(script, captions, hashtags, design_assets, state)

        # Execute publishing across platforms
        results = await self._execute_publishing(plan, design_briefs, state)

        publish_schedule = plan.get("publish_plan", {})

        return {
            "publish_schedule": publish_schedule,
            "publish_results": results,
            "current_agent": "publisher",
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def _create_publish_plan(
        self, script: dict, captions: list, hashtags: list, assets: list, state: dict
    ) -> dict:
        """Use LLM to create an optimized publishing plan."""
        analytics = state.get("analytics", {})

        user_message = f"""Create an optimized publishing plan for the following content.

## Script
{json.dumps(script, indent=2, default=str)}

## Captions Available
{json.dumps(captions[:5], indent=2, default=str) if captions else "No pre-written captions."}

## Hashtags Available
{json.dumps(hashtags[:30], indent=2, default=str) if hashtags else "No hashtags available."}

## Design Assets Available
{json.dumps(assets[:10], indent=2, default=str) if assets else "No design assets yet."}

## Previous Analytics (for optimal timing)
{json.dumps(analytics, indent=2, default=str) if analytics else "No previous analytics."}

## Instructions
1. Plan publication for ALL relevant platforms
2. Set optimal posting times based on analytics (or use defaults if no data)
3. Customize captions for each platform's style
4. Distribute hashtags appropriately per platform
5. Note any platform-specific requirements

Return ONLY valid JSON."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=4096,
            )

            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()

            return json.loads(clean)

        except Exception as e:
            logger.error(f"[{self.display_name}] Publish planning failed: {e}")
            return {"publish_plan": {"content_title": "Unknown", "platforms": []}}

    async def _execute_publishing(self, plan: dict, design_briefs: list, state: dict) -> list:
        """Execute the publishing plan across all platforms."""
        results = []
        platforms_to_publish = plan.get("publish_plan", {}).get("platforms", [])

        for platform_plan in platforms_to_publish:
            platform_name = platform_plan.get("platform", "").lower()
            result = {
                "id": f"result-{uuid.uuid4().hex[:8]}",
                "platform": platform_name,
                "post_id": None,
                "post_url": None,
                "status": "pending",
                "published_at": None,
                "error": None,
            }

            try:
                platform_module_map = {
                    "instagram": ("platforms.instagram", "InstagramPlatform"),
                    "tiktok": ("platforms.tiktok", "TikTokPlatform"),
                    "youtube": ("platforms.youtube", "YouTubePlatform"),
                    "x": ("platforms.twitter", "TwitterPlatform"),
                    "twitter": ("platforms.twitter", "TwitterPlatform"),
                    "linkedin": ("platforms.linkedin", "LinkedInPlatform"),
                }

                if platform_name not in platform_module_map:
                    result["status"] = "failed"
                    result["error"] = f"Unknown platform: {platform_name}"
                    results.append(result)
                    continue

                module_path, class_name = platform_module_map[platform_name]
                module = __import__(module_path, fromlist=[class_name])
                platform_class = getattr(module, class_name)
                platform = platform_class()

                publish_result = await platform.publish(
                    content_type=platform_plan.get("content_type", "post"),
                    caption=platform_plan.get("caption", ""),
                    hashtags=platform_plan.get("hashtags", []),
                    assets=platform_plan.get("assets", []),
                )

                result["post_id"] = publish_result.get("post_id")
                result["post_url"] = publish_result.get("post_url")
                result["status"] = publish_result.get("status", "published")
                result["published_at"] = datetime.utcnow().isoformat()

                logger.info(f"[{self.display_name}] Published to {platform_name}: {result['status']}")

            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
                logger.error(f"[{self.display_name}] Failed to publish to {platform_name}: {e}")

            results.append(result)

        return results
