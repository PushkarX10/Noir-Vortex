"""
Instagram Platform Integration
Meta Graph API — OAuth, container-based uploads, metrics fetching.
"""

import logging
from typing import Optional

import httpx

from config import InstagramConfig

logger = logging.getLogger(__name__)


class InstagramPlatform:
    """Instagram Graph API integration for content publishing and analytics."""

    def __init__(self):
        self.config = InstagramConfig
        self.base_url = InstagramConfig.BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured()

    async def get_trending_content(self) -> dict:
        """Discover trending content on Instagram (via hashtag/explore endpoints)."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "Instagram API not configured. Add INSTAGRAM_ACCESS_TOKEN to .env",
                "sample_trends": [
                    {"type": "reel", "trend": "Quick transformation hooks", "engagement": "high"},
                    {"type": "carousel", "trend": "Educational slide decks", "engagement": "medium"},
                    {"type": "reel", "trend": "Behind-the-scenes content", "engagement": "high"},
                ]
            }

        try:
            # Search recent media by hashtag
            response = await self.client.get(
                f"{self.base_url}/ig_hashtag_search",
                params={
                    "user_id": self.config.BUSINESS_ACCOUNT_ID,
                    "q": "trending",
                    "access_token": self.config.ACCESS_TOKEN,
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Instagram trending fetch failed: {e}")
            return {"status": "error", "error": str(e)}

    async def publish(
        self,
        content_type: str = "post",
        caption: str = "",
        hashtags: list[str] | None = None,
        assets: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """
        Publish content to Instagram.
        Uses container-based upload: create container → publish container.
        """
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "Instagram API not configured. Post saved as draft.",
                "post_id": None,
                "post_url": None,
            }

        full_caption = caption
        if hashtags:
            full_caption += "\n\n" + " ".join(hashtags)

        try:
            if content_type in ("reel", "video"):
                return await self._publish_reel(full_caption, assets)
            elif content_type == "carousel":
                return await self._publish_carousel(full_caption, assets)
            else:
                return await self._publish_image(full_caption, assets)
        except Exception as e:
            logger.error(f"Instagram publish failed: {e}")
            return {"status": "failed", "error": str(e), "post_id": None, "post_url": None}

    async def _publish_image(self, caption: str, assets: list[str] | None) -> dict:
        """Publish a single image post."""
        image_url = assets[0] if assets else None
        if not image_url:
            return {"status": "failed", "error": "No image asset provided"}

        # Step 1: Create container
        container_resp = await self.client.post(
            f"{self.base_url}/{self.config.BUSINESS_ACCOUNT_ID}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": self.config.ACCESS_TOKEN,
            }
        )
        container_resp.raise_for_status()
        container_id = container_resp.json().get("id")

        # Step 2: Publish container
        publish_resp = await self.client.post(
            f"{self.base_url}/{self.config.BUSINESS_ACCOUNT_ID}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self.config.ACCESS_TOKEN,
            }
        )
        publish_resp.raise_for_status()
        post_id = publish_resp.json().get("id")

        return {
            "status": "published",
            "post_id": post_id,
            "post_url": f"https://www.instagram.com/p/{post_id}/",
        }

    async def _publish_reel(self, caption: str, assets: list[str] | None) -> dict:
        """Publish a Reel."""
        video_url = assets[0] if assets else None
        if not video_url:
            return {"status": "failed", "error": "No video asset provided"}

        container_resp = await self.client.post(
            f"{self.base_url}/{self.config.BUSINESS_ACCOUNT_ID}/media",
            params={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": self.config.ACCESS_TOKEN,
            }
        )
        container_resp.raise_for_status()
        container_id = container_resp.json().get("id")

        publish_resp = await self.client.post(
            f"{self.base_url}/{self.config.BUSINESS_ACCOUNT_ID}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self.config.ACCESS_TOKEN,
            }
        )
        publish_resp.raise_for_status()
        post_id = publish_resp.json().get("id")

        return {
            "status": "published",
            "post_id": post_id,
            "post_url": f"https://www.instagram.com/reel/{post_id}/",
        }

    async def _publish_carousel(self, caption: str, assets: list[str] | None) -> dict:
        """Publish a carousel post."""
        if not assets or len(assets) < 2:
            return {"status": "failed", "error": "Carousel requires at least 2 assets"}

        # Create containers for each item
        children_ids = []
        for asset_url in assets:
            resp = await self.client.post(
                f"{self.base_url}/{self.config.BUSINESS_ACCOUNT_ID}/media",
                params={
                    "image_url": asset_url,
                    "is_carousel_item": True,
                    "access_token": self.config.ACCESS_TOKEN,
                }
            )
            resp.raise_for_status()
            children_ids.append(resp.json().get("id"))

        # Create carousel container
        container_resp = await self.client.post(
            f"{self.base_url}/{self.config.BUSINESS_ACCOUNT_ID}/media",
            params={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": caption,
                "access_token": self.config.ACCESS_TOKEN,
            }
        )
        container_resp.raise_for_status()
        container_id = container_resp.json().get("id")

        publish_resp = await self.client.post(
            f"{self.base_url}/{self.config.BUSINESS_ACCOUNT_ID}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self.config.ACCESS_TOKEN,
            }
        )
        publish_resp.raise_for_status()
        post_id = publish_resp.json().get("id")

        return {
            "status": "published",
            "post_id": post_id,
            "post_url": f"https://www.instagram.com/p/{post_id}/",
        }

    async def get_post_metrics(self, post_ids: list[str]) -> dict:
        """Fetch metrics for specific posts."""
        if not self.is_configured:
            return {"status": "not_configured"}

        metrics_data = []
        for post_id in post_ids:
            try:
                resp = await self.client.get(
                    f"{self.base_url}/{post_id}/insights",
                    params={
                        "metric": "impressions,reach,engagement,saved,shares",
                        "access_token": self.config.ACCESS_TOKEN,
                    }
                )
                resp.raise_for_status()
                metrics_data.append({"post_id": post_id, "metrics": resp.json()})
            except Exception as e:
                metrics_data.append({"post_id": post_id, "error": str(e)})

        return {"platform": "instagram", "posts": metrics_data}

    async def get_account_metrics(self) -> dict:
        """Fetch account-level metrics."""
        if not self.is_configured:
            return {"status": "not_configured"}

        try:
            resp = await self.client.get(
                f"{self.base_url}/{self.config.BUSINESS_ACCOUNT_ID}/insights",
                params={
                    "metric": "impressions,reach,follower_count",
                    "period": "day",
                    "access_token": self.config.ACCESS_TOKEN,
                }
            )
            resp.raise_for_status()
            return {"platform": "instagram", "account_metrics": resp.json()}
        except Exception as e:
            return {"platform": "instagram", "status": "error", "error": str(e)}

    async def close(self):
        await self.client.aclose()
