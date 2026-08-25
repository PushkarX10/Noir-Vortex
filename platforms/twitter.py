"""
X (Twitter) Platform Integration
X API v2 — OAuth 2.0, tweet/thread creation, trending, engagement metrics.
"""

import logging

import httpx

from config import TwitterConfig

logger = logging.getLogger(__name__)


class TwitterPlatform:
    """X (Twitter) API v2 integration."""

    def __init__(self):
        self.config = TwitterConfig
        self.base_url = TwitterConfig.BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured()

    def _headers(self, use_bearer: bool = True) -> dict:
        if use_bearer:
            return {
                "Authorization": f"Bearer {self.config.BEARER_TOKEN}",
                "Content-Type": "application/json",
            }
        return {
            "Authorization": f"OAuth oauth_consumer_key=\"{self.config.API_KEY}\"",
            "Content-Type": "application/json",
        }

    async def get_trending_content(self) -> dict:
        """Discover trending topics and tweets on X."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "X/Twitter API not configured. Add X_BEARER_TOKEN to .env",
                "sample_trends": [
                    {"type": "tweet", "trend": "Contrarian takes on tech", "engagement": "high"},
                    {"type": "thread", "trend": "Breakdown threads with data", "engagement": "viral"},
                    {"type": "tweet", "trend": "Hot take + proof formula", "engagement": "high"},
                ]
            }

        try:
            # Get trending topics
            resp = await self.client.get(
                f"{self.base_url}/trends/by/woeid/1",  # Worldwide
                headers=self._headers(),
            )
            resp.raise_for_status()

            # Also search recent viral tweets
            search_resp = await self.client.get(
                f"{self.base_url}/tweets/search/recent",
                headers=self._headers(),
                params={
                    "query": "min_retweets:1000 min_likes:5000 lang:en",
                    "max_results": 10,
                    "tweet.fields": "public_metrics,created_at",
                }
            )
            search_resp.raise_for_status()

            return {
                "platform": "twitter",
                "trends": resp.json(),
                "viral_tweets": search_resp.json(),
            }

        except Exception as e:
            logger.error(f"X/Twitter trending fetch failed: {e}")
            return {"status": "error", "error": str(e)}

    async def publish(
        self,
        content_type: str = "tweet",
        caption: str = "",
        hashtags: list[str] | None = None,
        assets: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Publish a tweet or thread to X."""
        if not self.is_configured or not self.config.ACCESS_TOKEN:
            return {
                "status": "not_configured",
                "message": "X API write access not configured. Tweet saved as draft.",
                "post_id": None,
                "post_url": None,
            }

        text = caption
        if hashtags:
            tag_text = " ".join(hashtags[:5])  # X works best with fewer hashtags
            if len(text) + len(tag_text) + 1 <= 280:
                text += "\n" + tag_text

        # Truncate to character limit
        if len(text) > 280:
            text = text[:277] + "..."

        try:
            if content_type == "thread":
                return await self._publish_thread(text, assets)
            else:
                return await self._publish_tweet(text, assets)
        except Exception as e:
            logger.error(f"X/Twitter publish failed: {e}")
            return {"status": "failed", "error": str(e), "post_id": None, "post_url": None}

    async def _publish_tweet(self, text: str, assets: list[str] | None) -> dict:
        """Publish a single tweet."""
        payload = {"text": text}

        resp = await self.client.post(
            f"{self.base_url}/tweets",
            headers=self._headers(use_bearer=False),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        tweet_id = data.get("data", {}).get("id")

        return {
            "status": "published",
            "post_id": tweet_id,
            "post_url": f"https://x.com/i/status/{tweet_id}",
        }

    async def _publish_thread(self, text: str, assets: list[str] | None) -> dict:
        """Publish a thread (multiple tweets in reply chain)."""
        # Split text into thread segments (~270 chars each with numbering)
        segments = self._split_into_thread(text)
        tweet_ids = []
        reply_to = None

        for i, segment in enumerate(segments):
            payload = {"text": segment}
            if reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}

            resp = await self.client.post(
                f"{self.base_url}/tweets",
                headers=self._headers(use_bearer=False),
                json=payload,
            )
            resp.raise_for_status()
            tweet_id = resp.json().get("data", {}).get("id")
            tweet_ids.append(tweet_id)
            reply_to = tweet_id

        return {
            "status": "published",
            "post_id": tweet_ids[0] if tweet_ids else None,
            "post_url": f"https://x.com/i/status/{tweet_ids[0]}" if tweet_ids else None,
            "thread_ids": tweet_ids,
        }

    def _split_into_thread(self, text: str, max_chars: int = 270) -> list[str]:
        """Split long text into thread-sized segments."""
        if len(text) <= max_chars:
            return [text]

        segments = []
        sentences = text.replace("\n", " ").split(". ")
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) + 2 <= max_chars:
                current += (". " if current else "") + sentence
            else:
                if current:
                    segments.append(current.strip() + ".")
                current = sentence

        if current:
            segments.append(current.strip())

        # Add numbering
        total = len(segments)
        if total > 1:
            segments = [f"{i+1}/{total} {seg}" for i, seg in enumerate(segments)]

        return segments

    async def get_post_metrics(self, post_ids: list[str]) -> dict:
        """Fetch metrics for specific tweets."""
        if not self.is_configured:
            return {"status": "not_configured"}

        try:
            resp = await self.client.get(
                f"{self.base_url}/tweets",
                headers=self._headers(),
                params={
                    "ids": ",".join(post_ids),
                    "tweet.fields": "public_metrics,created_at",
                }
            )
            resp.raise_for_status()
            return {"platform": "twitter", "tweets": resp.json()}
        except Exception as e:
            return {"platform": "twitter", "status": "error", "error": str(e)}

    async def get_account_metrics(self) -> dict:
        """Fetch account-level metrics."""
        if not self.is_configured:
            return {"status": "not_configured"}
        return {"platform": "twitter", "account_metrics": {"status": "requires_user_id"}}

    async def close(self):
        await self.client.aclose()
