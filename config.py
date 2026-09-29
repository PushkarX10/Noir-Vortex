"""
The Loop — Central Configuration
Loads environment variables, sets defaults, and exposes typed config.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).parent
load_dotenv(_PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------
class LLMConfig:
    PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    MODEL = os.getenv("LLM_MODEL", "")

    # Provider-specific defaults
    DEFAULTS = {
        "openai": "gpt-4o",
        "anthropic": "claude-sonnet-4-20250514",
        "google": "gemini-3.5-flash",
    }

    # API keys (LiteLLM reads these from env automatically)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    @classmethod
    def get_model(cls) -> str:
        if cls.MODEL:
            return cls.MODEL
        return cls.DEFAULTS.get(cls.PROVIDER, cls.DEFAULTS["openai"])

    @classmethod
    def has_valid_key(cls) -> bool:
        return any([cls.OPENAI_API_KEY, cls.ANTHROPIC_API_KEY, cls.GOOGLE_API_KEY])


# ---------------------------------------------------------------------------
# Platform Credentials
# ---------------------------------------------------------------------------
class InstagramConfig:
    ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    BASE_URL = "https://graph.facebook.com/v20.0"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.ACCESS_TOKEN and cls.BUSINESS_ACCOUNT_ID)


class TikTokConfig:
    ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
    CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
    BASE_URL = "https://open.tiktokapis.com/v2"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.ACCESS_TOKEN)


class YouTubeConfig:
    API_KEY = os.getenv("YOUTUBE_API_KEY", "")
    CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
    CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
    REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.API_KEY)


class TwitterConfig:
    API_KEY = os.getenv("X_API_KEY", "")
    API_SECRET = os.getenv("X_API_SECRET", "")
    BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")
    ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
    ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "")
    BASE_URL = "https://api.x.com/2"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.BEARER_TOKEN)


class RedditConfig:
    CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    USER_AGENT = os.getenv("REDDIT_USER_AGENT", "TheLoop/1.0")

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.CLIENT_ID and cls.CLIENT_SECRET)


class LinkedInConfig:
    ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    ORGANIZATION_ID = os.getenv("LINKEDIN_ORGANIZATION_ID", "")
    BASE_URL = "https://api.linkedin.com/v2"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.ACCESS_TOKEN)


# ---------------------------------------------------------------------------
# Brand Assets
# ---------------------------------------------------------------------------
class BrandConfig:
    """Default brand assets — configurable via dashboard settings."""
    PRIMARY_COLOR = "#0A0A0F"       # Ink black
    SECONDARY_COLOR = "#1E3A5F"     # Deep blue
    ACCENT_COLOR = "#00D4FF"        # Electric cyan accent
    BACKGROUND_COLOR = "#0D0D12"    # Dark background
    TEXT_COLOR = "#E8E8ED"          # Light text
    FONT_PRIMARY = "SF Pro Display"
    FONT_FALLBACK = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    LOGO_PATH = ""  # Set via settings

    @classmethod
    def to_dict(cls) -> dict:
        return {
            "primary_color": cls.PRIMARY_COLOR,
            "secondary_color": cls.SECONDARY_COLOR,
            "accent_color": cls.ACCENT_COLOR,
            "background_color": cls.BACKGROUND_COLOR,
            "text_color": cls.TEXT_COLOR,
            "font_primary": cls.FONT_PRIMARY,
            "font_fallback": cls.FONT_FALLBACK,
            "logo_path": cls.LOGO_PATH,
        }


# ---------------------------------------------------------------------------
# Application Settings
# ---------------------------------------------------------------------------
class AppConfig:
    HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/theloop.db")
    CONTENT_OUTPUT_DIR = os.getenv("CONTENT_OUTPUT_DIR", "./output")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Pipeline defaults
    MAX_HOOKS_PER_IDEA = 10
    MAX_RETRIES_PER_AGENT = 3
    APPROVAL_TIMEOUT_HOURS = 24

    @classmethod
    def ensure_dirs(cls):
        """Create required directories if they don't exist."""
        Path(cls.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(cls.CONTENT_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
