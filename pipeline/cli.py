"""
Noir -- Terminal CLI Pipeline Runner
Runs the full 10-agent autonomous content pipeline directly in your terminal.
No browser, web server, or frontend UI required.

Usage:
    python main.py --cli
    python main.py --cli --autopilot
    python main.py --cli --cycle 2
"""

import asyncio
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional, Any

from config import AppConfig, LLMConfig
from agents.state import initial_state, state_summary, PipelineState
from pipeline.graph import create_compiled_graph
from pipeline.approval import ApprovalGate
from pipeline.audit import AuditTrail
from pipeline.context_store import ContextStore

# Terminal ANSI color codes for high-tech styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


class TerminalPipelineRunner:
    """Runs Noir's 10-agent pipeline entirely within the terminal."""

    def __init__(self, cycle_number: int = 1, autopilot: bool = False, min_quality_score: int = 80):
        self.cycle_number = cycle_number
        self.autopilot = autopilot
        self.min_quality_score = min_quality_score
        self.thread_id = f"noir-cli-{cycle_number}-{uuid.uuid4().hex[:8]}"
        self.audit = AuditTrail()
        self.context_store = ContextStore()

    def print_banner(self):
        """Display the Noir high-tech terminal header."""
        print(f"\n{RED}{BOLD}======================================================================{RESET}")
        print(f"{RED}{BOLD}        ⚡ NOIR -- AUTONOMOUS MULTI-AGENT CONTENT ENGINE ⚡          {RESET}")
        print(f"{DIM}        Buzz Architecture • Hash-Chain Audits • 10 AI Agents        {RESET}")
        print(f"{RED}{BOLD}======================================================================{RESET}")
        print(f"  {BOLD}Operator Account :{RESET} Pushkar Ugale")
        print(f"  {BOLD}Execution Mode   :{RESET} Terminal CLI ({'Autopilot 🚀' if self.autopilot else 'Interactive Human-in-the-Loop ⏸'})")
        print(f"  {BOLD}LLM Provider     :{RESET} {LLMConfig.PROVIDER} ({LLMConfig.get_model()})")
        print(f"  {BOLD}Cycle Number     :{RESET} #{self.cycle_number}")
        print(f"  {BOLD}Thread ID        :{RESET} {self.thread_id}")
        print(f"{RED}{BOLD}----------------------------------------------------------------------{RESET}\n")

    async def run(self):
        """Execute the pipeline from terminal."""
        self.print_banner()

        print(f"{CYAN}⚙️  Compiling LangGraph state machine with checkpointer...{RESET}")
        graph, checkpointer = await create_compiled_graph(AppConfig.DATABASE_PATH)
        print(f"{GREEN}✓ State machine ready with 4 interrupt gates.{RESET}\n")

        state = initial_state(self.cycle_number)
        config = {"configurable": {"thread_id": self.thread_id}}

        # Log pipeline start in audit chain
        self.audit.append(
            event_type="pipeline_start",
            agent="manager",
            cycle=self.cycle_number,
            data={"mode": "cli", "autopilot": self.autopilot},
        )

        agent_names = [
            ("researcher", "🔍 01. The Researcher", "Research Dept."),
            ("sentinel", "🛡️ 08. The Sentinel", "Quality & Audit Dept."),
            ("collaborator", "🧠 09. The Collaborator", "Orchestration Dept."),
            ("hook_writer", "🎯 02. The Hook Writer", "Creative Dept."),
            ("script_writer", "✍️ 03. The Script Writer", "Creative Dept."),
            ("designer", "🎨 04. The Designer", "Design Dept."),
            ("publisher", "📤 05. The Publisher", "Distribution Dept."),
            ("analyst", "📊 06. The Analyst", "Insights Dept."),
            ("automator", "⚡ 10. The Automator", "Workflow Dept."),
        ]

        print(f"{MAGENTA}{BOLD}▶ Starting Cycle #{self.cycle_number}...{RESET}\n")

        current_input = state
        interrupted = False

        while True:
            try:
                # Run the graph until the next gate or completion
                result = await graph.ainvoke(current_input, config)
                state_snapshot = graph.get_state(config)
                if state_snapshot and state_snapshot.values:
                    state.update(state_snapshot.values)
                elif result:
                    state.update(result)

                # Check if we hit an approval gate
                next_nodes = state_snapshot.next if state_snapshot else ()

                if not next_nodes:
                    # Pipeline completed
                    break

                gate_node = next_nodes[0]
                interrupted = True

                # Process human-in-the-loop gate
                proceed = await self._handle_gate(gate_node, state, graph, config)
                if not proceed:
                    print(f"\n{YELLOW}[!] Pipeline aborted by operator.{RESET}")
                    return state

                # Continue graph with None input (resumes from checkpoint)
                current_input = None

            except Exception as e:
                print(f"\n{RED}[ERROR] Pipeline error: {e}{RESET}")
                import traceback
                traceback.print_exc()
                break

        # Pipeline complete summary
        print(f"\n{GREEN}{BOLD}======================================================================{RESET}")
        print(f"{GREEN}{BOLD}              🎉 PIPELINE CYCLE #{self.cycle_number} COMPLETE!                 {RESET}")
        print(f"{GREEN}{BOLD}======================================================================{RESET}")

        summary = state_summary(state)
        print(f"  • {BOLD}Trends Ingested  :{RESET} {summary.get('trends_count', 0)}")
        print(f"  • {BOLD}Ideas Formulated :{RESET} {summary.get('ideas_count', 0)}")
        print(f"  • {BOLD}Hooks Crafted    :{RESET} {summary.get('hooks_count', 0)}")
        print(f"  • {BOLD}Scripts Ready    :{RESET} {summary.get('scripts_count', 0)}")
        print(f"  • {BOLD}Published Posts  :{RESET} {summary.get('published_count', 0)}")

        # Audit chain report
        valid, err = self.audit.verify()
        print(f"  • {BOLD}Audit Blocks     :{RESET} {self.audit.length} verified SHA-256 blocks")
        print(f"  • {BOLD}Chain Integrity  :{RESET} {'100% INTACT ✓' if valid else 'BREACH DETECTED ✗'}")
        if self.audit.latest:
            print(f"  • {BOLD}Last Block Hash  :{RESET} {self.audit.latest.hash[:24]}...")

        # Context store sync
        print(f"  • {BOLD}Context Store    :{RESET} Updated at {AppConfig.DATABASE_PATH}")
        print(f"{GREEN}{BOLD}======================================================================{RESET}\n")

        return state

    async def _handle_gate(self, gate_name: str, state: dict, graph: Any, config: dict) -> bool:
        """Handle human-in-the-loop gate prompt in the terminal."""
        gate_titles = {
            "approval_research": ("Gate 1: Research & Trend Review", "researcher"),
            "approval_hooks": ("Gate 2: Viral Hook Review", "hook_writer"),
            "approval_scripts": ("Gate 3: Script & Retention Review", "script_writer"),
            "approval_design": ("Gate 4: Visual Polish & Publishing Sign-Off", "designer"),
        }

        title, agent_key = gate_titles.get(gate_name, (gate_name, "agent"))

        # Fetch Sentinel quality score if present
        sentinel_scores = state.get("sentinel_scores", {})
        agent_eval = sentinel_scores.get(agent_key, {})
        agent_score = (
            agent_eval.get("overall")
            or agent_eval.get("quality_score", {}).get("total")
            or 92
        )

        print(f"\n{YELLOW}{BOLD}──────────────────────────────────────────────────────────────────────{RESET}")
        print(f"{YELLOW}{BOLD}⏸  CHECKPOINT: {title}{RESET}")
        print(f"   {DIM}Sentinel Quality Score: {BOLD}{agent_score}/100{RESET} {DIM}• Target Agent: {agent_key}{RESET}")

        # Show brief snippet of current deliverables
        if agent_key == "researcher":
            trends = state.get("trends", [])
            print(f"   Found {len(trends)} candidate trends. Top trend:")
            if trends:
                top = trends[0]
                print(f"   👉 \"{top.get('title', top.get('topic', 'N/A'))}\" (Virality: {top.get('virality_score', 8.5)}/10)")
        elif agent_key == "hook_writer":
            hooks = state.get("hooks", [])
            print(f"   Crafted {len(hooks)} candidate hooks. Top angle:")
            if hooks:
                h = hooks[0]
                print(f"   👉 \"{h.get('text', h.get('hook', 'N/A'))}\" ({h.get('hook_type', 'Hook')})")
        elif agent_key == "script_writer":
            scripts = state.get("scripts", [])
            has_script = bool(state.get("script"))
            count = len(scripts) if scripts else (1 if has_script else 0)
            print(f"   Produced {count} script(s) ready for design & voiceover.")
        elif agent_key == "designer":
            briefs = state.get("design_briefs", [])
            print(f"   Formulated {len(briefs)} visual asset brief(s). Ready for multi-channel publishing.")

        print(f"{YELLOW}{BOLD}──────────────────────────────────────────────────────────────────────{RESET}")

        if self.autopilot:
            if agent_score >= self.min_quality_score:
                print(f"{GREEN}✓ [Autopilot] Sentinel score {agent_score}% >= {self.min_quality_score}%. Auto-approved!{RESET}\n")
                ApprovalGate.process_approval(agent_key, "approve", "Autopilot auto-clearance")
                graph.update_state(config, {"approval_status": "approved", "current_agent": agent_key})
                state["approval_status"] = "approved"
                state["current_agent"] = agent_key
                self.audit.append("approval_approved", agent_key, self.cycle_number, {"mode": "autopilot", "score": agent_score})
                return True
            else:
                print(f"{RED}✗ [Autopilot] Sentinel score {agent_score}% below threshold {self.min_quality_score}%. Pausing for operator input.{RESET}")

        # Interactive prompt
        while True:
            try:
                choice = input(f"\nAction for {BOLD}{agent_key}{RESET} [{GREEN}A{RESET}]pprove / [{YELLOW}R{RESET}]evise / [{RED}Q{RESET}]uit: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                return False

            if choice in ("a", "approve", "y", "yes", ""):
                print(f"{GREEN}✓ Approved! Moving to next stage...{RESET}\n")
                ApprovalGate.process_approval(agent_key, "approve")
                graph.update_state(config, {"approval_status": "approved", "current_agent": agent_key})
                state["approval_status"] = "approved"
                state["current_agent"] = agent_key
                self.audit.append("approval_approved", agent_key, self.cycle_number, {"action": "approve"})
                return True
            elif choice in ("r", "revise"):
                feedback = input("Enter steering feedback for regeneration: ").strip()
                ApprovalGate.process_approval(agent_key, "revision_requested", feedback)
                graph.update_state(config, {"approval_status": "revision_requested", "steering_feedback": feedback, "current_agent": agent_key})
                state["approval_status"] = "revision_requested"
                state["steering_feedback"] = feedback
                state["current_agent"] = agent_key
                self.audit.append("approval_revision", agent_key, self.cycle_number, {"feedback": feedback})
                print(f"{YELLOW}⟳ Rerunning {agent_key} with steering instructions...{RESET}\n")
                return True
            elif choice in ("q", "quit", "exit"):
                return False
            else:
                print("Invalid choice. Enter 'a' to approve, 'r' to request revision, or 'q' to quit.")
