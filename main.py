"""
Noir — Autonomous Multi-Agent Content Engine
Terminal Application Entry Point.

Runs the 10-agent pipeline directly in the terminal with interactive
human-in-the-loop approval gates or fully autonomous autopilot mode.

Usage:
    python main.py                  # Interactive Human-in-the-Loop CLI
    python main.py --autopilot      # Autonomous execution (auto-clears quality gates)
    python main.py --cycle 2        # Run specific cycle number
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(_project_root))

# If running outside .venv and dependencies are missing, auto-delegate to project .venv
_venv_python = (
    _project_root / ".venv" / "Scripts" / "python.exe"
    if sys.platform == "win32"
    else _project_root / ".venv" / "bin" / "python"
)
if _venv_python.exists() and Path(sys.executable).resolve() != _venv_python.resolve():
    try:
        from langgraph.graph import StateGraph  # noqa: F401
    except (ImportError, ModuleNotFoundError):
        import subprocess
        sys.exit(subprocess.call([str(_venv_python)] + sys.argv, cwd=str(_project_root)))


# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import AppConfig, LLMConfig
from pipeline.cli import TerminalPipelineRunner


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


def main():
    """Start Noir in Terminal CLI mode."""
    parser = argparse.ArgumentParser(
        description="Noir -- Autonomous Multi-Agent Content Engine (Terminal CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                  # Run interactive terminal pipeline
    python main.py --autopilot      # Run fully autonomous without manual pause
    python main.py --cycle 2        # Run cycle #2
    python main.py --threshold 85   # Set minimum Sentinel score for autopilot
        """,
    )
    parser.add_argument(
        "--autopilot",
        "-a",
        action="store_true",
        help="Run without interactive approval prompts (auto-approves gates meeting Sentinel threshold)",
    )
    parser.add_argument(
        "--cycle",
        type=int,
        default=1,
        help="Pipeline cycle number to run (default: 1)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=80,
        help="Minimum Sentinel quality score required for autopilot auto-clearance (default: 80)",
    )
    args = parser.parse_args()

    setup_logging()
    AppConfig.ensure_dirs()

    # Run terminal pipeline runner
    runner = TerminalPipelineRunner(
        cycle_number=args.cycle,
        autopilot=args.autopilot,
        min_quality_score=args.threshold,
    )
    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
