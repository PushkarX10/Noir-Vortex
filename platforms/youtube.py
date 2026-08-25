"""
YouTube Platform Integration
YouTube Data API v3 — video uploads, Shorts, trending, analytics.
"""

import logging
from pathlib import Path

import httpx

from config import YouTubeConfig

logger = logging.getLogger(__name__)


class YouTubePlatform:
    """YouTube Data API v3 integration."""

    def __init__(self):
        self.config = YouTubeConfig
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.upload_url = "https://www.googleapis.com/upload/youtube/v3/videos"
        self.client = httpx.AsyncClient(timeout=120.0)

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured()

    async def get_trending_content(self) -> dict:
        """Discover trending YouTube Shorts and videos."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "YouTube API not configured. Add YOUTUBE_API_KEY to .env",
                "sample_trends": [
                    {"type": "short", "trend": "60-second tutorials", "engagement": "high"},
                    {"type": "short", "trend": "Before/after transformations", "engagement": "viral"},
                    {"type": "video", "trend": "Deep-dive breakdowns", "engagement": "medium"},
                ]
            }

        try:
            response = await self.client.get(
                f"{self.base_url}/videos",
                params={
                    "part": "snippet,statistics",
                    "chart": "mostPopular",
                    "regionCode": "US",
                    "maxResults": 20,
                    "key": self.config.API_KEY,
                }
            )
            response.raise_for_status()
            data = response.json()

            trending = []
            for item in data.get("items", []):
                trending.append({
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "views": item["statistics"].get("viewCount", 0),
                    "likes": item["statistics"].get("likeCount", 0),
                    "comments": item["statistics"].get("commentCount", 0),
                    "published_at": item["snippet"]["publishedAt"],
                })

            return {"platform": "youtube", "trending": trending}

        except Exception as e:
            logger.error(f"YouTube trending fetch failed: {e}")
            return {"status": "error", "error": str(e)}

    async def publish(
        self,
        content_type: str = "short",
        caption: str = "",
        hashtags: list[str] | None = None,
        assets: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """
        Upload a video to YouTube.
        For Shorts: video must be vertical (9:16) and <= 60 seconds.
        """
        if not self.is_configured or not self.config.REFRESH_TOKEN:
            return {
                "status": "not_configured",
                "message": "YouTube upload requires OAuth credentials. Video saved as draft.",
                "post_id": None,
                "post_url": None,
            }

        title = caption[:100] if caption else "New Upload"
        description = caption
        if hashtags:
            description += "\n\n" + " ".join(hashtags)
            # Add #Shorts tag for Shorts
            if content_type == "short" and "#Shorts" not in description:
                description += " #Shorts"

        try:
            # Get fresh access token from refresh token
            access_token = await self._refresh_access_token()

            video_path = assets[0] if assets else None
            if not video_path:
                return {"status": "failed", "error": "No video asset provided"}

            # Initiate resumable upload
            init_resp = await self.client.post(
                f"{self.upload_url}?uploadType=resumable&part=snippet,status",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "snippet": {
                        "title": title,
                        "description": description,
                        "categoryId": "22",  # People & Blogs
                    },
                    "status": {
                        "privacyStatus": "public",
                        "selfDeclaredMadeForKids": False,
                    }
                }
            )
            init_resp.raise_for_status()

            upload_url = init_resp.headers.get("location")
            if not upload_url:
                return {"status": "failed", "error": "No upload URL returned"}

            # Upload the video file
            if Path(video_path).exists():
                with open(video_path, "rb") as f:
                    upload_resp = await self.client.put(
                        upload_url,
                        headers={"Content-Type": "video/*"},
                        content=f.read(),
                    )
                    upload_resp.raise_for_status()
                    data = upload_resp.json()
                    video_id = data.get("id")

                    return {
                        "status": "published",
                        "post_id": video_id,
                        "post_url": f"https://youtube.com/shorts/{video_id}" if content_type == "short"
                                    else f"https://youtube.com/watch?v={video_id}",
                    }
            else:
                return {"status": "failed", "error": f"Video file not found: {video_path}"}

        except Exception as e:
            logger.error(f"YouTube publish failed: {e}")
            return {"status": "failed", "error": str(e), "post_id": None, "post_url": None}

    async def _refresh_access_token(self) -> str:
        """Exchange refresh token for a fresh access token."""
        resp = await self.client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.config.CLIENT_ID,
                "client_secret": self.config.CLIENT_SECRET,
                "refresh_token": self.config.REFRESH_TOKEN,
                "grant_type": "refresh_token",
            }
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def get_post_metrics(self, post_ids: list[str]) -> dict:
        """Fetch metrics for specific videos."""
        if not self.is_configured:
            return {"status": "not_configured"}

        try:
            resp = await self.client.get(
                f"{self.base_url}/videos",
                params={
                    "part": "statistics,contentDetails",
                    "id": ",".join(post_ids),
                    "key": self.config.API_KEY,
                }
            )
            resp.raise_for_status()
            return {"platform": "youtube", "videos": resp.json().get("items", [])}
        except Exception as e:
            return {"platform": "youtube", "status": "error", "error": str(e)}

    async def get_account_metrics(self) -> dict:
        """Fetch channel-level metrics."""
        if not self.is_configured:
            return {"status": "not_configured"}

        try:
            resp = await self.client.get(
                f"{self.base_url}/channels",
                params={
                    "part": "statistics",
                    "mine": True,
                    "key": self.config.API_KEY,
                }
            )
            resp.raise_for_status()
            return {"platform": "youtube", "account_metrics": resp.json()}
        except Exception as e:
            return {"platform": "youtube", "status": "error", "error": str(e)}

    async def close(self):
        await self.client.aclose()
