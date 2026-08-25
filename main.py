"""
The Loop — Application Entry Point
Starts the FastAPI server with the LangGraph pipeline.

Usage:
    python main.py
    
Or directly with uvicorn:
    uvicorn dashboard.app:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import AppConfig


def setup_logging():
    """Configure logging for the application."""
    log_level = getattr(logging, AppConfig.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def main():
    """Start The Loop."""
    setup_logging()
    logger = logging.getLogger("theloop")

    # Ensure required directories exist
    AppConfig.ensure_dirs()

    logger.info("================================================")
    logger.info("     NOIR - Autonomous Content Engine           ")
    logger.info("     7 Agents | 4 Approval Gates | 1 Pipeline   ")
    logger.info("================================================")

    # Check LLM configuration
    from config import LLMConfig
    if LLMConfig.has_valid_key():
        logger.info(f"  LLM Provider : {LLMConfig.PROVIDER}")
        logger.info(f"  LLM Model    : {LLMConfig.get_model()}")
    else:
        logger.warning("  [!] No LLM API key configured!")
        logger.warning("      Copy .env.example to .env and add your API key.")
        logger.warning("      The dashboard will still load, but agents cannot run.")
    
    logger.info(f"  Database     : {AppConfig.DATABASE_PATH}")
    logger.info(f"  Output Dir   : {AppConfig.CONTENT_OUTPUT_DIR}")
    logger.info(f"  Dashboard    : http://{AppConfig.HOST}:{AppConfig.PORT}")
    logger.info("")

    # Start the server
    import uvicorn
    uvicorn.run(
        "dashboard.app:app",
        host=AppConfig.HOST,
        port=AppConfig.PORT,
        reload=False,
        log_level=AppConfig.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
