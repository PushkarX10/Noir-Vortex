"""
LinkedIn Platform Integration
LinkedIn Marketing API — post/article publishing, engagement metrics.
"""

import logging

import httpx

from config import LinkedInConfig

logger = logging.getLogger(__name__)


class LinkedInPlatform:
    """LinkedIn Marketing API integration."""

    def __init__(self):
        self.config = LinkedInConfig
        self.base_url = LinkedInConfig.BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    async def get_trending_content(self) -> dict:
        """LinkedIn doesn't have a public trending API — return guidance."""
        return {
            "status": "limited",
            "message": "LinkedIn doesn't expose a trending content API. "
                       "The Researcher uses LLM knowledge of LinkedIn trends instead.",
            "sample_trends": [
                {"type": "post", "trend": "Founder journey posts", "engagement": "high"},
                {"type": "article", "trend": "Industry insight threads", "engagement": "medium"},
                {"type": "post", "trend": "Data-driven hot takes", "engagement": "high"},
            ]
        }

    async def publish(
        self,
        content_type: str = "post",
        caption: str = "",
        hashtags: list[str] | None = None,
        assets: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Publish a post or article to LinkedIn."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "LinkedIn API not configured. Post saved as draft.",
                "post_id": None,
                "post_url": None,
            }

        text = caption
        if hashtags:
            text += "\n\n" + " ".join(hashtags[:10])  # LinkedIn supports more hashtags

        try:
            # Get user URN
            me_resp = await self.client.get(
                f"{self.base_url}/me",
                headers=self._headers(),
            )
            me_resp.raise_for_status()
            person_urn = f"urn:li:person:{me_resp.json().get('id')}"

            # Create post
            payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
                },
            }

            resp = await self.client.post(
                f"{self.base_url}/ugcPosts",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            post_id = resp.json().get("id")

            return {
                "status": "published",
                "post_id": post_id,
                "post_url": f"https://www.linkedin.com/feed/update/{post_id}/",
            }

        except Exception as e:
            logger.error(f"LinkedIn publish failed: {e}")
            return {"status": "failed", "error": str(e), "post_id": None, "post_url": None}

    async def get_post_metrics(self, post_ids: list[str]) -> dict:
        """Fetch metrics for specific LinkedIn posts."""
        if not self.is_configured:
            return {"status": "not_configured"}

        metrics_data = []
        for post_id in post_ids:
            try:
                resp = await self.client.get(
                    f"{self.base_url}/socialActions/{post_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                metrics_data.append({"post_id": post_id, "metrics": resp.json()})
            except Exception as e:
                metrics_data.append({"post_id": post_id, "error": str(e)})

        return {"platform": "linkedin", "posts": metrics_data}

    async def get_account_metrics(self) -> dict:
        """Fetch account-level metrics."""
        if not self.is_configured:
            return {"status": "not_configured"}

        try:
            resp = await self.client.get(
                f"{self.base_url}/me",
                headers=self._headers(),
                params={"projection": "(id,firstName,lastName)"},
            )
            resp.raise_for_status()
            return {"platform": "linkedin", "account": resp.json()}
        except Exception as e:
            return {"platform": "linkedin", "status": "error", "error": str(e)}

    async def close(self):
        await self.client.aclose()
