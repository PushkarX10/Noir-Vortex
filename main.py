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
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
import asyncio


def main():
    """Start Noir in Web Dashboard or Terminal CLI mode."""
    parser = argparse.ArgumentParser(
        description="Noir -- Autonomous Multi-Agent Content Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                  # Start FastAPI web dashboard & React UI
    python main.py --cli            # Run 10-agent pipeline directly in terminal
    python main.py --cli --autopilot # Run end-to-end fully autonomous without pauses
    python main.py --cli --cycle 2  # Run cycle #2 from terminal
        """,
    )
    parser.add_argument(
        "--cli",
        "-c",
        action="store_true",
        help="Run pipeline directly in terminal (no browser or web server required)",
    )
    parser.add_argument(
        "--autopilot",
        "-a",
        action="store_true",
        help="Run without interactive approval prompts (auto-approve gates clearing quality threshold)",
    )
    parser.add_argument(
        "--cycle",
        type=int,
        default=1,
        help="Cycle number to run (default: 1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=AppConfig.PORT,
        help=f"Web server port (default: {AppConfig.PORT})",
    )
    args = parser.parse_args()

    # Ensure required directories exist
    AppConfig.ensure_dirs()

    # Terminal CLI mode
    if args.cli or args.autopilot:
        from pipeline.cli import TerminalPipelineRunner
        runner = TerminalPipelineRunner(
            cycle_number=args.cycle,
            autopilot=args.autopilot,
        )
        asyncio.run(runner.run())
        return

    # Web Dashboard mode
    setup_logging()
    logger = logging.getLogger("noir")

    logger.info("================================================")
    logger.info("     ⚡ NOIR - Autonomous Content Engine         ")
    logger.info("     10 Agents | Buzz Architecture | 4 Gates    ")
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
    logger.info(f"  Dashboard    : http://{AppConfig.HOST}:{args.port}")
    logger.info("  CLI Mode     : Run 'python main.py --cli' for terminal-only")
    logger.info("")

    # Start the server
    import uvicorn
    uvicorn.run(
        "dashboard.app:app",
        host=AppConfig.HOST,
        port=args.port,
        reload=False,
        log_level=AppConfig.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()

