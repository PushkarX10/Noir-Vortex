"""
Reddit Platform Integration
Reddit API via PRAW — subreddit monitoring, trending discovery, niche analysis.
Read-only: used by the Researcher agent for content discovery.
"""

import logging

from config import RedditConfig

logger = logging.getLogger(__name__)


class RedditPlatform:
    """Reddit API integration for content research and niche discovery."""

    def __init__(self):
        self.config = RedditConfig
        self._reddit = None

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured()

    def _get_reddit(self):
        """Lazy-load PRAW Reddit instance."""
        if self._reddit is None:
            try:
                import praw
                self._reddit = praw.Reddit(
                    client_id=self.config.CLIENT_ID,
                    client_secret=self.config.CLIENT_SECRET,
                    user_agent=self.config.USER_AGENT,
                )
            except ImportError:
                logger.error("PRAW not installed. Install with: pip install praw")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Reddit: {e}")
                return None
        return self._reddit

    async def get_trending_content(self) -> dict:
        """Discover trending posts and subreddits for content ideas."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "Reddit API not configured. Add REDDIT_CLIENT_ID to .env",
                "sample_trends": [
                    {"subreddit": "r/Entrepreneur", "trend": "Solo founder success stories", "engagement": "high"},
                    {"subreddit": "r/SideProject", "trend": "Build in public journeys", "engagement": "medium"},
                    {"subreddit": "r/Marketing", "trend": "AI content strategy debates", "engagement": "viral"},
                ]
            }

        reddit = self._get_reddit()
        if not reddit:
            return {"status": "error", "error": "Failed to connect to Reddit"}

        try:
            trending_data = {
                "platform": "reddit",
                "popular_posts": [],
                "trending_subreddits": [],
            }

            # Get popular posts from key subreddits
            target_subs = [
                "Entrepreneur", "Marketing", "SocialMedia",
                "ContentCreation", "SideProject", "Startups"
            ]

            for sub_name in target_subs:
                try:
                    subreddit = reddit.subreddit(sub_name)
                    for post in subreddit.hot(limit=5):
                        trending_data["popular_posts"].append({
                            "subreddit": f"r/{sub_name}",
                            "title": post.title,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "upvote_ratio": post.upvote_ratio,
                            "url": f"https://reddit.com{post.permalink}",
                            "created_utc": str(post.created_utc),
                            "is_self": post.is_self,
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch r/{sub_name}: {e}")

            # Get trending/popular subreddits
            try:
                for sub in reddit.subreddits.popular(limit=10):
                    trending_data["trending_subreddits"].append({
                        "name": sub.display_name,
                        "subscribers": sub.subscribers,
                        "description": sub.public_description[:200] if sub.public_description else "",
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch popular subreddits: {e}")

            return trending_data

        except Exception as e:
            logger.error(f"Reddit trending fetch failed: {e}")
            return {"status": "error", "error": str(e)}

    async def search_niche(self, query: str, limit: int = 10) -> dict:
        """Search for subreddits and posts related to a specific niche."""
        reddit = self._get_reddit()
        if not reddit:
            return {"status": "not_configured"}

        try:
            results = {
                "query": query,
                "subreddits": [],
                "posts": [],
            }

            # Search subreddits
            for sub in reddit.subreddits.search(query, limit=5):
                results["subreddits"].append({
                    "name": sub.display_name,
                    "subscribers": sub.subscribers,
                    "description": sub.public_description[:200] if sub.public_description else "",
                })

            # Search posts
            for post in reddit.subreddit("all").search(query, sort="top", time_filter="week", limit=limit):
                results["posts"].append({
                    "subreddit": str(post.subreddit),
                    "title": post.title,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": f"https://reddit.com{post.permalink}",
                })

            return results

        except Exception as e:
            logger.error(f"Reddit niche search failed: {e}")
            return {"status": "error", "error": str(e)}

    async def get_post_metrics(self, post_ids: list[str]) -> dict:
        """Reddit doesn't support post-level metrics API in the same way."""
        return {"platform": "reddit", "status": "read_only", "message": "Reddit is used for research only."}

    async def get_account_metrics(self) -> dict:
        """Reddit account metrics (limited)."""
        return {"platform": "reddit", "status": "read_only", "message": "Reddit is used for research only."}

    async def publish(self, **kwargs) -> dict:
        """Reddit publishing not supported — read-only research platform."""
        return {
            "status": "not_supported",
            "message": "Reddit is a research-only platform in The Loop. No publishing.",
            "post_id": None,
            "post_url": None,
        }
