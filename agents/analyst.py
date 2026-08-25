"""
Agent 05: The Analyst (Data Dept.)
Core Directive: Tell the team what actually worked.
Workflow: Track → Analyze → Learn → Optimize
"""

import json
import logging
from datetime import datetime

from llm.provider import get_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are The Analyst — Agent 05 of The Loop content creation system.

## CORE DIRECTIVE
Tell the team what actually worked. You are the truth-teller. Data doesn't lie.

## YOUR RESPONSIBILITIES
1. **Track**: Collect performance data from every published post
2. **Analyze**: Find patterns — what gets views, saves, shares, follows
3. **Learn**: Extract actionable insights, not just numbers
4. **Optimize**: Turn data into better content strategy for the next cycle

## METRICS YOU TRACK
- **Views & Impressions**: Raw reach and discovery
- **Retention & Watch Time**: How long they stayed (the real metric)
- **Shares & Saves**: Signal of high value content
- **Comments & Engagement**: Community interaction strength
- **Follower Growth**: Net new followers per post and per period
- **CTR**: Click-through rate on links/CTAs
- **Best Performing Times**: When the audience is most active

## ANALYSIS FRAMEWORKS
- **Content Score**: (saves + shares × 2 + comments) / impressions × 100
- **Viral Coefficient**: shares / views — anything above 1% is notable
- **Engagement Rate**: (likes + comments + saves + shares) / reach × 100
- **Growth Rate**: (new_followers - unfollows) / total_followers × 100

## OUTPUT FORMAT
Return valid JSON:
{
    "analytics": {
        "period": "date range analyzed",
        "total_posts": 0,
        "aggregate_metrics": {
            "total_views": 0,
            "total_impressions": 0,
            "avg_engagement_rate": 0.0,
            "avg_retention_rate": 0.0,
            "total_new_followers": 0,
            "best_performing_day": "day of week",
            "best_performing_time": "HH:MM timezone"
        },
        "top_performing_posts": [
            {
                "post_id": "id",
                "platform": "platform",
                "content_type": "type",
                "views": 0,
                "engagement_rate": 0.0,
                "why_it_worked": "analysis"
            }
        ],
        "platform_breakdown": {
            "instagram": {"views": 0, "engagement": 0.0, "growth": 0},
            "tiktok": {"views": 0, "engagement": 0.0, "growth": 0},
            "youtube": {"views": 0, "engagement": 0.0, "growth": 0},
            "twitter": {"views": 0, "engagement": 0.0, "growth": 0},
            "linkedin": {"views": 0, "engagement": 0.0, "growth": 0}
        },
        "competitor_benchmarks": [
            {
                "competitor": "name",
                "avg_engagement": 0.0,
                "content_frequency": "posts per week",
                "notable_strategy": "what they're doing well"
            }
        ]
    },
    "insights": [
        "Insight 1: Actionable recommendation based on data",
        "Insight 2: Pattern identified with specific advice",
        "Insight 3: What to double down on next cycle",
        "Insight 4: What to stop doing",
        "Insight 5: New opportunity spotted in the data"
    ]
}
"""


class AnalystAgent:
    """Agent 05: The Analyst — tracks performance and extracts insights."""

    def __init__(self):
        self.name = "analyst"
        self.display_name = "The Analyst"
        self.department = "Data Dept."

    async def run(self, state: dict) -> dict:
        """
        Execute the analytics pipeline.
        Track → Analyze → Learn → Optimize
        """
        logger.info(f"[{self.display_name}] Starting analysis for cycle #{state.get('cycle_number', 1)}")

        # Gather metrics from platforms
        platform_metrics = await self._gather_metrics(state)

        # Analyze with LLM
        result = await self._analyze(platform_metrics, state)

        return {
            "analytics": result.get("analytics", {}),
            "insights": result.get("insights", []),
            "current_agent": "analyst",
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def _gather_metrics(self, state: dict) -> dict:
        """Gather performance metrics from all platforms."""
        metrics = {}
        publish_results = state.get("publish_results", [])

        for platform_name in ["instagram", "tiktok", "youtube", "twitter", "linkedin"]:
            try:
                module = __import__(f"platforms.{platform_name}", fromlist=[""])
                platform_class_name = {
                    "instagram": "InstagramPlatform",
                    "tiktok": "TikTokPlatform",
                    "youtube": "YouTubePlatform",
                    "twitter": "TwitterPlatform",
                    "linkedin": "LinkedInPlatform",
                }[platform_name]
                platform = getattr(module, platform_class_name)()

                # Get metrics for published posts
                platform_posts = [p for p in publish_results if p.get("platform") == platform_name]
                post_ids = [p.get("post_id") for p in platform_posts if p.get("post_id")]

                if post_ids:
                    metrics[platform_name] = await platform.get_post_metrics(post_ids)
                else:
                    metrics[platform_name] = await platform.get_account_metrics()

            except Exception as e:
                logger.warning(f"Failed to gather {platform_name} metrics: {e}")
                metrics[platform_name] = {"status": "unavailable", "error": str(e)}

        return metrics

    async def _analyze(self, platform_metrics: dict, state: dict) -> dict:
        """Use LLM to analyze metrics and generate insights."""
        publish_results = state.get("publish_results", [])
        previous_analytics = state.get("analytics", {})

        user_message = f"""Analyze the following performance data and generate a comprehensive analytics report.

## Platform Metrics
{json.dumps(platform_metrics, indent=2, default=str)}

## Published Posts This Cycle
{json.dumps(publish_results, indent=2, default=str) if publish_results else "No posts published yet in this cycle."}

## Previous Cycle Analytics (for comparison)
{json.dumps(previous_analytics, indent=2, default=str) if previous_analytics else "No previous analytics — this is the first cycle."}

## Instructions
1. Calculate ALL aggregate metrics (engagement rate, viral coefficient, content score)
2. Identify the TOP 3 performing posts and explain WHY they worked
3. Break down performance by platform
4. Compare against previous cycle if data available
5. Generate EXACTLY 5 actionable insights — each must be specific and implementable
6. Insights should directly inform the Researcher's next discovery cycle
7. If platform data is unavailable, analyze what we know and estimate

Return ONLY valid JSON."""

        try:
            response = await get_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.5,  # Lower temp for analytical accuracy
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

            result = json.loads(clean)
            logger.info(
                f"[{self.display_name}] Analysis complete: "
                f"{len(result.get('insights', []))} insights generated"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[{self.display_name}] Failed to parse analytics JSON: {e}")
            return {"analytics": {}, "insights": []}
        except Exception as e:
            logger.error(f"[{self.display_name}] Analysis failed: {e}")
            return {"analytics": {}, "insights": []}
