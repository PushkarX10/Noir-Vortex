"""
Agent 01: The Researcher (Research Dept.)
Core Directive: Find every viral opportunity.
Workflow: Discover → Collect → Report
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are The Researcher — Agent 01 of The Loop content creation system.

## CORE DIRECTIVE
Find every viral opportunity. You are the eyes and ears of the operation.

## YOUR RESPONSIBILITIES
1. **Track Competitors**: Monitor top creators and brands in the niche
2. **Find Patterns**: Identify trends before they go viral
3. **Save Viral Posts**: Collect high-performing content for reference
4. **Discover Niches**: Find new, untapped content opportunities

## YOUR SOURCES
- Instagram Reels
- TikTok
- YouTube Shorts
- X (Twitter)
- Reddit

## YOUR WORKFLOW
1. DISCOVER: Find opportunities across all platforms
2. COLLECT: Gather insights, metrics, and examples
3. REPORT: Deliver structured recommendations

## OUTPUT FORMAT
You MUST return valid JSON with this structure:
{
    "trends": [
        {
            "id": "unique-id",
            "title": "Trend name",
            "platform": "tiktok|instagram|youtube|x|reddit",
            "description": "What the trend is about",
            "virality_score": 1-10,
            "growth_rate": "percentage or descriptor",
            "example_posts": ["url1", "url2"],
            "discovered_at": "ISO timestamp"
        }
    ],
    "content_ideas": [
        {
            "id": "unique-id",
            "title": "Content idea title",
            "description": "Detailed description of the content piece",
            "target_platform": "primary platform",
            "cross_post_to": ["other platforms"],
            "trend_connection": "which trend this connects to",
            "urgency": "high|medium|low",
            "estimated_reach": "low|medium|high|viral",
            "content_type": "reel|carousel|short|thread|post",
            "niche": "specific niche category"
        }
    ],
    "viral_references": [
        {
            "id": "unique-id",
            "platform": "platform name",
            "creator": "creator handle",
            "content_type": "type",
            "engagement_metrics": {
                "views": 0,
                "likes": 0,
                "shares": 0,
                "comments": 0,
                "saves": 0
            },
            "why_it_worked": "analysis of success factors",
            "replicable_elements": ["element1", "element2"]
        }
    ]
}
"""


class ResearcherAgent:
    """Agent 01: The Researcher — finds viral opportunities across platforms."""

    def __init__(self):
        self.name = "researcher"
        self.display_name = "The Researcher"
        self.department = "Research Dept."

    async def run(self, state: dict) -> dict:
        """
        Execute the research pipeline.
        Discover → Collect → Report
        """
        logger.info(f"[{self.display_name}] Starting research cycle #{state.get('cycle_number', 1)}")

        # Gather platform data
        platform_data = await self._discover(state)

        # Generate research report via LLM
        report = await self._analyze_and_report(platform_data, state)

        # Update state with findings
        now = datetime.utcnow().isoformat()
        return {
            "trends": report.get("trends", []),
            "content_ideas": report.get("content_ideas", []),
            "viral_references": report.get("viral_references", []),
            "current_agent": "researcher",
            "approval_status": "pending",
            "updated_at": now,
        }

    async def _discover(self, state: dict) -> dict:
        """Discover opportunities from all platforms."""
        platform_data = {}

        # Import platform modules
        try:
            from platforms.instagram import InstagramPlatform
            ig = InstagramPlatform()
            platform_data["instagram"] = await ig.get_trending_content()
        except Exception as e:
            logger.warning(f"Instagram discovery failed: {e}")
            platform_data["instagram"] = {"status": "unavailable", "error": str(e)}

        try:
            from platforms.tiktok import TikTokPlatform
            tt = TikTokPlatform()
            platform_data["tiktok"] = await tt.get_trending_content()
        except Exception as e:
            logger.warning(f"TikTok discovery failed: {e}")
            platform_data["tiktok"] = {"status": "unavailable", "error": str(e)}

        try:
            from platforms.youtube import YouTubePlatform
            yt = YouTubePlatform()
            platform_data["youtube"] = await yt.get_trending_content()
        except Exception as e:
            logger.warning(f"YouTube discovery failed: {e}")
            platform_data["youtube"] = {"status": "unavailable", "error": str(e)}

        try:
            from platforms.twitter import TwitterPlatform
            tw = TwitterPlatform()
            platform_data["twitter"] = await tw.get_trending_content()
        except Exception as e:
            logger.warning(f"X/Twitter discovery failed: {e}")
            platform_data["twitter"] = {"status": "unavailable", "error": str(e)}

        try:
            from platforms.reddit import RedditPlatform
            rd = RedditPlatform()
            platform_data["reddit"] = await rd.get_trending_content()
        except Exception as e:
            logger.warning(f"Reddit discovery failed: {e}")
            platform_data["reddit"] = {"status": "unavailable", "error": str(e)}

        return platform_data

    async def _analyze_and_report(self, platform_data: dict, state: dict) -> dict:
        """Use LLM to analyze platform data and generate structured report."""
        previous_insights = state.get("insights", [])

        user_message = f"""Analyze the following platform data and generate a comprehensive research report.

## Platform Data
{json.dumps(platform_data, indent=2, default=str)}

## Previous Cycle Insights (use these to refine your research)
{json.dumps(previous_insights, indent=2) if previous_insights else "No previous insights — this is the first cycle."}

## Instructions
1. Identify the TOP 5 most promising trends across all platforms
2. Generate 5-8 specific, actionable content ideas based on these trends
3. Highlight 3-5 viral reference posts worth studying
4. Assign unique IDs (use format: trend-001, idea-001, ref-001)
5. Be specific about WHY each trend is worth pursuing
6. Consider cross-platform potential for each idea

Return ONLY valid JSON matching the required output format."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.8,
                max_tokens=4096,
            )

            # Parse JSON response
            # Handle potential markdown code blocks
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()

            report = json.loads(clean)

            # Ensure IDs exist
            for trend in report.get("trends", []):
                if "id" not in trend:
                    trend["id"] = f"trend-{uuid.uuid4().hex[:8]}"
                if "discovered_at" not in trend:
                    trend["discovered_at"] = datetime.utcnow().isoformat()

            for idea in report.get("content_ideas", []):
                if "id" not in idea:
                    idea["id"] = f"idea-{uuid.uuid4().hex[:8]}"

            for ref in report.get("viral_references", []):
                if "id" not in ref:
                    ref["id"] = f"ref-{uuid.uuid4().hex[:8]}"

            logger.info(
                f"[{self.display_name}] Report generated: "
                f"{len(report.get('trends', []))} trends, "
                f"{len(report.get('content_ideas', []))} ideas, "
                f"{len(report.get('viral_references', []))} references"
            )
            return report

        except json.JSONDecodeError as e:
            logger.error(f"[{self.display_name}] Failed to parse LLM response as JSON: {e}")
            return {
                "trends": [],
                "content_ideas": [],
                "viral_references": [],
            }
        except Exception as e:
            logger.error(f"[{self.display_name}] Research analysis failed: {e}")
            return {
                "trends": [],
                "content_ideas": [],
                "viral_references": [],
            }
