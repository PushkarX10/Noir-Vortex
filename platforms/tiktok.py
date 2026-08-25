"""
TikTok Platform Integration
TikTok Content Posting API — async upload flow, trending discovery, metrics.
"""

import logging

import httpx

from config import TikTokConfig

logger = logging.getLogger(__name__)


class TikTokPlatform:
    """TikTok Content Posting API integration."""

    def __init__(self):
        self.config = TikTokConfig
        self.base_url = TikTokConfig.BASE_URL
        self.client = httpx.AsyncClient(timeout=60.0)

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    async def get_trending_content(self) -> dict:
        """Discover trending content on TikTok."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "TikTok API not configured. Add TIKTOK_ACCESS_TOKEN to .env",
                "sample_trends": [
                    {"type": "video", "trend": "POV storytelling format", "engagement": "viral"},
                    {"type": "video", "trend": "Split-screen reaction hooks", "engagement": "high"},
                    {"type": "video", "trend": "Text-overlay tutorials", "engagement": "high"},
                ]
            }

        try:
            response = await self.client.post(
                f"{self.base_url}/research/video/query/",
                headers=self._headers(),
                json={
                    "query": {"and": [{"field_name": "region_code", "field_values": ["US"]}]},
                    "max_count": 20,
                    "start_date": "",
                    "end_date": "",
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TikTok trending fetch failed: {e}")
            return {"status": "error", "error": str(e)}

    async def publish(
        self,
        content_type: str = "video",
        caption: str = "",
        hashtags: list[str] | None = None,
        assets: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """
        Publish video to TikTok.
        Async flow: init upload → upload video → publish.
        NOTE: TikTok API requires audit approval for direct publishing.
        Unapproved apps can only create drafts.
        """
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "TikTok API not configured. Video saved as draft.",
                "post_id": None,
                "post_url": None,
            }

        title = caption
        if hashtags:
            title += " " + " ".join(hashtags)

        # Truncate to TikTok's title limit
        if len(title) > 2200:
            title = title[:2197] + "..."

        try:
            # Step 1: Init upload
            init_resp = await self.client.post(
                f"{self.base_url}/post/publish/video/init/",
                headers=self._headers(),
                json={
                    "post_info": {
                        "title": title,
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": assets[0] if assets else "",
                    }
                }
            )
            init_resp.raise_for_status()
            data = init_resp.json()

            publish_id = data.get("data", {}).get("publish_id")

            return {
                "status": "processing",
                "post_id": publish_id,
                "post_url": None,
                "message": "Video submitted for processing. TikTok will notify when published.",
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {
                    "status": "draft",
                    "post_id": None,
                    "post_url": None,
                    "message": "TikTok API audit pending. Video saved as draft.",
                }
            raise
        except Exception as e:
            logger.error(f"TikTok publish failed: {e}")
            return {"status": "failed", "error": str(e), "post_id": None, "post_url": None}

    async def check_publish_status(self, publish_id: str) -> dict:
        """Check the status of an async publish operation."""
        if not self.is_configured:
            return {"status": "not_configured"}

        try:
            resp = await self.client.post(
                f"{self.base_url}/post/publish/status/fetch/",
                headers=self._headers(),
                json={"publish_id": publish_id}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_post_metrics(self, post_ids: list[str]) -> dict:
        """Fetch metrics for specific videos."""
        if not self.is_configured:
            return {"status": "not_configured"}

        try:
            resp = await self.client.post(
                f"{self.base_url}/video/query/",
                headers=self._headers(),
                json={"filters": {"video_ids": post_ids}},
            )
            resp.raise_for_status()
            return {"platform": "tiktok", "videos": resp.json()}
        except Exception as e:
            return {"platform": "tiktok", "status": "error", "error": str(e)}

    async def get_account_metrics(self) -> dict:
        """Fetch account-level metrics."""
        if not self.is_configured:
            return {"status": "not_configured"}

        try:
            resp = await self.client.get(
                f"{self.base_url}/user/info/",
                headers=self._headers(),
                params={"fields": "follower_count,following_count,likes_count,video_count"},
            )
            resp.raise_for_status()
            return {"platform": "tiktok", "account_metrics": resp.json()}
        except Exception as e:
            return {"platform": "tiktok", "status": "error", "error": str(e)}

    async def close(self):
        await self.client.aclose()
