"""
The Loop â€” FastAPI Dashboard Application
REST API + WebSocket for real-time agent monitoring and approval management.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from config import AppConfig, LLMConfig, BrandConfig
from agents.state import initial_state, state_summary
from pipeline.approval import ApprovalGate
from pipeline.scheduler import PipelineScheduler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Noir",
    description="Autonomous Multi-Agent Content Creation System",
    version="1.0.0",
)

# Enable CORS for Vite dev server / external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
_dashboard_dir = Path(__file__).parent
_vortex_dist = _dashboard_dir.parent / "VortexUI-main" / "dist"

app.mount("/static", StaticFiles(directory=_dashboard_dir / "static"), name="static")

if (_vortex_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=_vortex_dist / "assets"), name="vortex_assets")

templates = Jinja2Templates(directory=_dashboard_dir / "templates")

# ---------------------------------------------------------------------------
# Global state (in-memory for the dashboard)
# ---------------------------------------------------------------------------
class PipelineManager:
    """Manages pipeline state and WebSocket connections."""

    def __init__(self):
        self.graph = None
        self.checkpointer = None
        self.current_thread_id: str = ""
        self.current_state: dict = {}
        self.pipeline_running: bool = False
        self.websocket_connections: list[WebSocket] = []
        self.scheduler = PipelineScheduler()
        self.history: list[dict] = []

    async def initialize(self):
        """Initialize the pipeline graph."""
        try:
            from pipeline.graph import create_compiled_graph
            self.graph, self.checkpointer = await create_compiled_graph(AppConfig.DATABASE_PATH)
            logger.info("[PipelineManager] Initialized successfully")
        except Exception as e:
            logger.error(f"[PipelineManager] Failed to initialize graph: {e}")
            self.graph = None

    async def start_pipeline(self, cycle_number: int = 1) -> dict:
        """Start a new pipeline cycle."""
        if self.pipeline_running:
            return {"status": "already_running", "message": "Pipeline is already running."}

        self.current_thread_id = f"loop-cycle-{cycle_number}-{uuid.uuid4().hex[:8]}"
        self.current_state = initial_state(cycle_number)
        self.pipeline_running = True

        await self._broadcast({
            "type": "pipeline_started",
            "cycle": cycle_number,
            "thread_id": self.current_thread_id,
        })

        # Run the pipeline in background
        asyncio.create_task(self._run_pipeline())

        return {
            "status": "started",
            "thread_id": self.current_thread_id,
            "cycle": cycle_number,
        }

    async def _run_pipeline(self):
        """Execute the pipeline graph until it hits an interrupt."""
        if not self.graph:
            logger.error("[PipelineManager] Graph not initialized!")
            self.pipeline_running = False
            return

        config = {"configurable": {"thread_id": self.current_thread_id}}

        try:
            await self._broadcast({
                "type": "agent_started",
                "agent": "researcher",
                "message": "The Researcher is discovering viral opportunities...",
            })

            # Run until first interrupt
            result = await self.graph.ainvoke(self.current_state, config)
            self.current_state.update(result)

            await self._broadcast({
                "type": "approval_required",
                "agent": self.current_state.get("current_agent", "unknown"),
                "state": state_summary(self.current_state),
            })

        except Exception as e:
            logger.error(f"[PipelineManager] Pipeline execution error: {e}")
            self.current_state["error_message"] = str(e)
            await self._broadcast({
                "type": "pipeline_error",
                "error": str(e),
            })
        finally:
            self.pipeline_running = False

    async def process_approval(self, action: str, feedback: str = "") -> dict:
        """Process a human approval action and resume the pipeline."""
        if not self.graph:
            return {"status": "error", "message": "Pipeline not initialized"}

        current_agent = self.current_state.get("current_agent", "")
        update = ApprovalGate.process_approval(current_agent, action, feedback)
        self.current_state.update(update)

        # Log to history
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": current_agent,
            "action": action,
            "feedback": feedback,
        })

        if action == "approve":
            # Resume the pipeline
            self.pipeline_running = True
            config = {"configurable": {"thread_id": self.current_thread_id}}

            next_agent = None
            from agents.manager import ManagerAgent
            mgr = ManagerAgent()
            next_agent = mgr.get_agent_after(current_agent)

            await self._broadcast({
                "type": "approval_processed",
                "action": action,
                "agent": current_agent,
                "next_agent": next_agent,
                "message": f"{current_agent} approved! Moving to {next_agent or 'end'}...",
            })

            # Resume in background
            asyncio.create_task(self._resume_pipeline())

        else:
            await self._broadcast({
                "type": "approval_processed",
                "action": action,
                "agent": current_agent,
                "message": f"{current_agent} sent back for revision.",
            })

            # Re-run the current agent with feedback
            self.pipeline_running = True
            asyncio.create_task(self._resume_pipeline())

        return {"status": "processed", "action": action, "agent": current_agent}

    async def _resume_pipeline(self):
        """Resume pipeline execution after an approval."""
        if not self.graph:
            self.pipeline_running = False
            return

        config = {"configurable": {"thread_id": self.current_thread_id}}

        try:
            agent = self.current_state.get("current_agent", "unknown")
            await self._broadcast({
                "type": "agent_started",
                "agent": agent,
                "message": f"Agent '{agent}' is working...",
            })

            result = await self.graph.ainvoke(self.current_state, config)
            self.current_state.update(result)

            # Check if pipeline completed
            if self.current_state.get("current_agent") == "analyst":
                await self._broadcast({
                    "type": "pipeline_completed",
                    "cycle": self.current_state.get("cycle_number", 0),
                    "state": state_summary(self.current_state),
                })
            else:
                await self._broadcast({
                    "type": "approval_required",
                    "agent": self.current_state.get("current_agent", "unknown"),
                    "state": state_summary(self.current_state),
                })

        except Exception as e:
            logger.error(f"[PipelineManager] Resume error: {e}")
            self.current_state["error_message"] = str(e)
            await self._broadcast({"type": "pipeline_error", "error": str(e)})
        finally:
            self.pipeline_running = False

    async def _broadcast(self, message: dict):
        """Broadcast a message to all connected WebSocket clients."""
        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.websocket_connections.remove(ws)


# Global pipeline manager
pipeline_mgr = PipelineManager()


# ---------------------------------------------------------------------------
# Lifecycle events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    AppConfig.ensure_dirs()
    await pipeline_mgr.initialize()
    logger.info("========================================")
    logger.info("     NOIR - System Online               ")
    logger.info("     Dashboard: http://localhost:8000   ")
    logger.info("========================================")


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
@app.get("/approvals", response_class=HTMLResponse)
@app.get("/analytics", response_class=HTMLResponse)
@app.get("/settings", response_class=HTMLResponse)
async def dashboard_spa(request: Request):
    """Serve VortexUI React Single Page Application."""
    index_file = _vortex_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    # Fallback to Jinja templates
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "state": state_summary(pipeline_mgr.current_state) if pipeline_mgr.current_state else {},
            "pipeline_running": pipeline_mgr.pipeline_running,
            "llm_provider": LLMConfig.PROVIDER,
            "llm_model": LLMConfig.get_model(),
            "has_llm_key": LLMConfig.has_valid_key(),
        }
    )


@app.get("/classic", response_class=HTMLResponse)
async def dashboard_classic(request: Request):
    """Classic Jinja2 dashboard page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "state": state_summary(pipeline_mgr.current_state) if pipeline_mgr.current_state else {},
            "pipeline_running": pipeline_mgr.pipeline_running,
            "llm_provider": LLMConfig.PROVIDER,
            "llm_model": LLMConfig.get_model(),
            "has_llm_key": LLMConfig.has_valid_key(),
        }
    )


@app.get("/approval", response_class=HTMLResponse)
async def approval_page(request: Request):
    """Approval review page."""
    index_file = _vortex_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    current_agent = pipeline_mgr.current_state.get("current_agent", "")
    review_data = ApprovalGate.get_review_data(current_agent, pipeline_mgr.current_state)
    return templates.TemplateResponse(
        request=request,
        name="approval.html",
        context={
            "review": review_data,
            "state": pipeline_mgr.current_state,
            "gates": ApprovalGate.get_all_gates(),
        }
    )


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
@app.post("/api/pipeline/start")
async def api_start_pipeline(cycle: int = 1):
    """Start a new pipeline cycle."""
    result = await pipeline_mgr.start_pipeline(cycle)
    return JSONResponse(result)


@app.post("/api/pipeline/stop")
async def api_stop_pipeline():
    """Stop the current pipeline."""
    pipeline_mgr.pipeline_running = False
    return JSONResponse({"status": "stopped"})


@app.get("/api/pipeline/status")
async def api_pipeline_status():
    """Get current pipeline status."""
    from agents.manager import ManagerAgent
    mgr = ManagerAgent()

    if pipeline_mgr.current_state:
        status = mgr.get_status_report(pipeline_mgr.current_state)
    else:
        status = {"status": "idle", "message": "No pipeline running"}

    status["pipeline_running"] = pipeline_mgr.pipeline_running
    return JSONResponse(status)


@app.get("/api/state")
async def api_get_state():
    """Get the full current pipeline state."""
    return JSONResponse(pipeline_mgr.current_state or {"status": "empty"})


@app.get("/api/state/summary")
async def api_get_state_summary():
    """Get a summary of the current pipeline state."""
    if pipeline_mgr.current_state:
        return JSONResponse(state_summary(pipeline_mgr.current_state))
    return JSONResponse({"status": "empty"})


@app.post("/api/approve")
async def api_approve(action: str = Form("approve"), feedback: str = Form("")):
    """Process an approval action."""
    if action not in ("approve", "reject", "revision_requested"):
        raise HTTPException(400, f"Invalid action: {action}")
    result = await pipeline_mgr.process_approval(action, feedback)
    return JSONResponse(result)


@app.get("/api/approval/review")
async def api_get_review_data():
    """Get the current approval review data."""
    current_agent = pipeline_mgr.current_state.get("current_agent", "")
    if not current_agent:
        return JSONResponse({"status": "no_pending_review"})
    review = ApprovalGate.get_review_data(current_agent, pipeline_mgr.current_state)
    return JSONResponse(review)


@app.get("/api/agents")
async def api_get_agents():
    """Get the list of all agents and their current status."""
    from agents.manager import ManagerAgent
    mgr = ManagerAgent()

    if pipeline_mgr.current_state:
        report = mgr.get_status_report(pipeline_mgr.current_state)
        return JSONResponse(report.get("agent_statuses", {}))

    return JSONResponse({
        "researcher": "idle",
        "hook_writer": "idle",
        "script_writer": "idle",
        "designer": "idle",
        "publisher": "idle",
        "analyst": "idle",
    })


@app.get("/api/history")
async def api_get_history():
    """Get approval history."""
    return JSONResponse(pipeline_mgr.history)




# ---------------------------------------------------------------------------
# Buzz-Integrated API Routes (Sentinel, Audit, Workflows, Context)
# ---------------------------------------------------------------------------

@app.get("/api/sentinel/scores")
async def api_sentinel_scores():
    """Get current sentinel quality scores for all agents."""
    scores = pipeline_mgr.current_state.get("sentinel_scores", {})
    return JSONResponse(scores)


@app.get("/api/audit/trail")
async def api_audit_trail(agent: str = None, limit: int = 50):
    """Get the audit trail, optionally filtered by agent."""
    trail = pipeline_mgr.current_state.get("audit_trail", [])
    if agent:
        trail = [e for e in trail if e.get("agent") == agent]
    return JSONResponse(trail[-limit:])


@app.get("/api/audit/verify")
async def api_audit_verify():
    """Verify the integrity of the audit chain."""
    from agents.sentinel import SentinelAgent
    trail = pipeline_mgr.current_state.get("audit_trail", [])
    is_valid = SentinelAgent.verify_audit_chain(trail)
    return JSONResponse({
        "valid": is_valid,
        "entries": len(trail),
        "last_hash": trail[-1].get("hash", "")[:16] + "..." if trail else "empty",
    })


@app.get("/api/context/briefs")
async def api_context_briefs():
    """Get current cross-agent context briefs."""
    briefs = pipeline_mgr.current_state.get("context_briefs", {})
    return JSONResponse(briefs)


@app.get("/api/context/insights")
async def api_cross_agent_insights():
    """Get cross-agent insights."""
    insights = pipeline_mgr.current_state.get("cross_agent_insights", [])
    return JSONResponse(insights)


@app.get("/api/context/memory")
async def api_cycle_memory():
    """Get cycle memory (cross-run learning)."""
    memory = pipeline_mgr.current_state.get("cycle_memory", {})
    return JSONResponse(memory)


@app.get("/api/workflows")
async def api_get_workflows():
    """Get all workflow definitions."""
    workflows = pipeline_mgr.current_state.get("workflow_definitions", [])
    return JSONResponse(workflows)


@app.get("/api/workflows/recommendations")
async def api_schedule_recommendations():
    """Get schedule and automation recommendations."""
    recommendations = pipeline_mgr.current_state.get("schedule_recommendations", [])
    automation = pipeline_mgr.current_state.get("automation_insights", [])
    return JSONResponse({
        "schedule_recommendations": recommendations,
        "automation_insights": automation,
    })


@app.get("/api/agents")
async def api_get_agents_enhanced():
    """Get the list of all agents (original + Buzz) and their current status."""
    from agents.manager import ManagerAgent
    mgr = ManagerAgent()

    if pipeline_mgr.current_state:
        report = mgr.get_status_report(pipeline_mgr.current_state)
        statuses = report.get("agent_statuses", {})
    else:
        statuses = {}

    # Ensure all 10 agents are represented
    all_agents = [
        "researcher", "hook_writer", "script_writer", "designer",
        "publisher", "analyst", "sentinel", "collaborator", "automator",
    ]
    for agent in all_agents:
        if agent not in statuses:
            statuses[agent] = "idle"

    return JSONResponse(statuses)


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time pipeline updates."""
    await websocket.accept()
    pipeline_mgr.websocket_connections.append(websocket)
    logger.info(f"WebSocket connected. Total: {len(pipeline_mgr.websocket_connections)}")

    try:
        # Send current state on connect
        if pipeline_mgr.current_state:
            await websocket.send_json({
                "type": "state_sync",
                "state": state_summary(pipeline_mgr.current_state),
                "pipeline_running": pipeline_mgr.pipeline_running,
            })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        pipeline_mgr.websocket_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(pipeline_mgr.websocket_connections)}")

