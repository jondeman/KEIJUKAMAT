"""
KonseptiKeiju - Main Application Entry Point

This module provides:
1. FastAPI web server for the UI
2. CLI interface for direct runs
3. Background task management
"""

import asyncio
import subprocess
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.core.config import settings
from src.core.filesystem import RunPaths, read_json, slugify, write_text
from src.core.logger import configure_logging, get_logger
from src.orchestrator.producer import Producer

logger = get_logger(__name__)

# Store running tasks
running_tasks: dict[str, asyncio.Task] = {}



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    configure_logging()
    logger.info("KonseptiKeiju starting up")
    yield
    # Cancel any running tasks on shutdown
    for task in running_tasks.values():
        task.cancel()
    logger.info("KonseptiKeiju shutting down")


# Create FastAPI app
app = FastAPI(
    title="KonseptiKeiju",
    description="AI-powered branded entertainment concept generator",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: allow GitHub Pages frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jondeman.github.io",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=web_dir / "static"), name="static")


# Request/Response models
class ForgeRequest(BaseModel):
    """Request to start a new forge run."""
    company_name: str
    user_email: str
    access_code: str
    additional_context: str = ""


class ForgeResponse(BaseModel):
    """Response with run ID."""
    run_id: str
    message: str


class TestResponse(BaseModel):
    """Response for test run."""
    test_id: str
    message: str
    git_published: bool
    email_sent: bool
    errors: list[str] = []


class StatusResponse(BaseModel):
    """Status of a running or completed run."""
    run_id: str
    company_name: str
    current_phase: str
    progress: int
    error_message: str | None = None
    concepts: list[dict[str, Any]] | None = None
    download_url: str | None = None


# Routes
@app.get("/")
async def index():
    """Serve the main page."""
    index_path = web_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"message": "KonseptiKeiju API", "status": "running"})


@app.head("/")
async def index_head() -> Response:
    """Return OK for health checks that use HEAD."""
    return Response(status_code=200)


@app.get("/health")
async def health() -> JSONResponse:
    """Simple health check endpoint for Render."""
    return JSONResponse({"status": "ok"})


@app.head("/health")
async def health_head() -> Response:
    """Return OK for health checks that use HEAD."""
    return Response(status_code=200)


@app.get("/status.html")
async def status_page():
    """Serve the status page."""
    status_path = web_dir / "status.html"
    if status_path.exists():
        return FileResponse(status_path)
    raise HTTPException(status_code=404, detail="Status page not found")


@app.post("/api/forge", response_model=ForgeResponse)
async def start_forge(request: ForgeRequest, background_tasks: BackgroundTasks):
    """
    Start a new concept forge run.
    
    Returns immediately with a run_id that can be used to track progress.
    """
    logger.info("Forge request received", company=request.company_name)
    
    # Validate access code
    if settings.access_code and request.access_code != settings.access_code:
        raise HTTPException(status_code=401, detail="Invalid access code")
    
    if running_tasks:
        raise HTTPException(
            status_code=409,
            detail="Run already in progress. Please wait for it to finish.",
        )

    try:
        # Create producer (this creates the run)
        producer = await Producer.create(
            company_name=request.company_name,
            user_email=request.user_email,
            access_code=request.access_code,
            additional_context=request.additional_context,
        )
        
        run_id = producer.state.run_id
        
        # Start the run in background
        async def run_forge():
            try:
                await producer.run()
            except Exception as e:
                logger.error("Forge run failed", run_id=run_id, error=str(e))
            finally:
                running_tasks.pop(run_id, None)
        
        task = asyncio.create_task(run_forge())
        running_tasks[run_id] = task
        
        return ForgeResponse(
            run_id=run_id,
            message="Forge started successfully",
        )
        
    except Exception as e:
        logger.error("Failed to start forge", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test", response_model=TestResponse)
async def run_system_test() -> TestResponse:
    """
    Run a lightweight system test:
    - Write a test file to docs/deliveries/_tests/{test_id}/
    - Push to GitHub (if configured)
    - Send a test email to a fixed recipient
    """
    test_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    errors: list[str] = []
    git_published = False
    email_sent = False

    test_dir = settings.get_delivery_pages_dir() / "_tests" / test_id
    test_file = test_dir / "test.md"
    test_body = (
        f"# KonseptiKeiju System Test\n\n"
        f"Test ID: {test_id}\n"
        f"Timestamp: {datetime.utcnow().isoformat()}Z\n\n"
        f"Tämä on automaattinen testiteksti Renderistä.\n"
    )
    await write_text(test_file, test_body)
    logger.info("System test file written", path=str(test_file), test_id=test_id)

    def _redact_secret(value: str, secret: str | None) -> str:
        if not value or not secret:
            return value
        redacted = value.replace(secret, "***")
        try:
            encoded = quote(secret, safe="")
            redacted = redacted.replace(encoded, "***")
        except Exception:
            pass
        return redacted

    token = settings.github_token
    repo = settings.github_repo
    if token and repo:
        try:
            repo_root = settings.project_root
            deliveries_dir = settings.get_delivery_pages_dir()
            encoded_token = quote(token, safe="")
            remote_url = f"https://x-access-token:{encoded_token}@github.com/{repo}.git"

            has_origin = subprocess.run(
                ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
                check=False,
                capture_output=True,
                text=True,
            )
            if has_origin.returncode != 0:
                subprocess.run(
                    ["git", "-C", str(repo_root), "remote", "add", "origin", remote_url],
                    check=True,
                )
            else:
                subprocess.run(
                    ["git", "-C", str(repo_root), "remote", "set-url", "origin", remote_url],
                    check=True,
                )

            if settings.git_user_name:
                subprocess.run(
                    ["git", "-C", str(repo_root), "config", "user.name", settings.git_user_name],
                    check=True,
                )
            if settings.git_user_email:
                subprocess.run(
                    ["git", "-C", str(repo_root), "config", "user.email", settings.git_user_email],
                    check=True,
                )
            if settings.git_user_name or settings.git_user_email:
                logger.info(
                    "System test git identity configured",
                    user_name=settings.git_user_name or "",
                    user_email=settings.git_user_email or "",
                )

            status = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "status",
                    "--porcelain",
                    "--untracked-files=all",
                    str(deliveries_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            changes = [line for line in status.stdout.splitlines() if line.strip()]
            if changes:
                subprocess.run(
                    ["git", "-C", str(repo_root), "add", str(deliveries_dir)],
                    check=True,
                )
                message = f"System test delivery: {test_id}"
                subprocess.run(
                    ["git", "-C", str(repo_root), "commit", "-m", message],
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", str(repo_root), "fetch", "origin", settings.github_branch],
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", str(repo_root), "rebase", "--autostash", f"origin/{settings.github_branch}"],
                    check=True,
                )
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repo_root),
                        "push",
                        "origin",
                        f"HEAD:{settings.github_branch}",
                    ],
                    check=True,
                )
                git_published = True
                logger.info("System test published to GitHub", file_count=len(changes))
            else:
                logger.info("System test publish skipped (no changes)", file_count=0)
        except Exception as exc:
            error_msg = _redact_secret(str(exc), token)
            errors.append(f"GitHub publish failed: {error_msg}")
            logger.error("System test GitHub publish failed", error=error_msg)
    else:
        errors.append("GitHub publish not configured")
        logger.warning("System test GitHub publish skipped (token/repo not configured)")

    try:
        from src.integrations.email.client import EmailClient

        subject = f"KonseptiKeiju Test — {test_id}"
        body = test_body
        client = EmailClient()
        logger.info(
            "System test email config",
            mode="sendgrid" if client.sendgrid_api_key else ("resend" if client.resend_api_key else "smtp"),
            host=client.host,
            port=client.port,
            user=repr(client.user),
            password_set=bool(client.password),
            sendgrid_from=client.sendgrid_from_email or "",
            sendgrid_key_set=bool(client.sendgrid_api_key),
            resend_from=client.resend_from_email or "",
            resend_key_set=bool(client.resend_api_key),
        )
        if not client._is_configured():
            errors.append("Email not configured (missing SendGrid/Resend/SMTP settings)")
            logger.warning("System test email skipped (email not configured)")
        else:
            email_sent = await client.send_delivery(
                to_email="joona.kortesmaki@gmail.com",
                subject=subject,
                body=body,
                attachments=None,
            )
            logger.info(
                "System test email result",
                to="joona.kortesmaki@gmail.com",
                sent=email_sent,
            )
            if email_sent:
                logger.info("System test email sent", to="joona.kortesmaki@gmail.com")
            else:
                errors.append("Email send failed (see Render logs for SMTP error)")
    except Exception as exc:
        errors.append(f"Email send failed: {exc}")
        logger.error("System test email failed", error=str(exc))

    return TestResponse(
        test_id=test_id,
        message="System test completed",
        git_published=git_published,
        email_sent=email_sent,
        errors=errors,
    )


@app.get("/api/status/{run_id}", response_model=StatusResponse)
async def get_status(run_id: str):
    """
    Get the status of a forge run.
    """
    # Find the run directory
    runs_dir = settings.get_runs_path()
    
    # Search for run directory (format: {date}_{slug}_{run_id})
    run_dir = None
    if runs_dir.exists():
        for d in runs_dir.iterdir():
            if d.is_dir() and d.name.endswith(f"_{run_id}"):
                run_dir = d
                break
    
    if not run_dir:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Load state
    state_file = run_dir / "run_state.json"
    if not state_file.exists():
        raise HTTPException(status_code=404, detail="Run state not found")
    
    try:
        state = await read_json(state_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read state: {e}")
    
    # Calculate progress
    progress_map = {
        "input": 0,
        "validate": 5,
        "check_archive": 10,
        "research": 30,
        "strategize": 40,
        "create": 60,
        "visualize": 80,
        "compose_pitch": 90,
        "package": 95,
        "deliver": 98,
        "done": 100,
        "error": -1,
    }
    
    current_phase = state.get("current_phase", "input")
    progress = progress_map.get(current_phase, 0)
    
    # Extract company name
    company_name = ""
    if state.get("user_input"):
        company_name = state["user_input"].get("company_name", "")
    
    # Extract concepts if done
    concepts = None
    if current_phase == "done" and state.get("concepts"):
        concepts = [
            {"id": c.get("id"), "title": c.get("title")}
            for c in state["concepts"]
        ]
    
    # Get error message if failed
    error_message = None
    if current_phase == "error" and state.get("phase_history"):
        last_phase = state["phase_history"][-1]
        error_message = last_phase.get("error_message")
    
    base_url = (settings.delivery_base_url or "").rstrip("/")
    company_slug = state.get("company_slug") if isinstance(state, dict) else None
    download_url = None
    if current_phase == "done":
        if base_url and company_slug:
            download_url = f"{base_url}/{company_slug}/{run_id}/outputs.zip"
        else:
            download_url = f"/api/download/{run_id}"

    return StatusResponse(
        run_id=run_id,
        company_name=company_name,
        current_phase=current_phase,
        progress=progress,
        error_message=error_message,
        concepts=concepts,
        download_url=download_url,
    )


@app.get("/api/logs/{run_id}")
async def get_logs(run_id: str, limit: int = 50):
    """
    Return recent log lines for a run.

    Args:
        run_id: Run identifier
        limit: Max number of log entries to return
    """
    runs_dir = settings.get_runs_path()

    run_dir = None
    if runs_dir.exists():
        for d in runs_dir.iterdir():
            if d.is_dir() and d.name.endswith(f"_{run_id}"):
                run_dir = d
                break

    if not run_dir:
        raise HTTPException(status_code=404, detail="Run not found")

    logs_file = run_dir / "logs.jsonl"
    entries: list[dict[str, Any]] = []

    if logs_file.exists():
        try:
            lines = logs_file.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read logs: {e}")

        import json

        for line in lines[-max(limit, 1):]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Fallback: synthesize entries from run_state.json if logs are empty
    if not entries:
        state_file = run_dir / "run_state.json"
        if state_file.exists():
            state = await read_json(state_file)
            history = state.get("phase_history") or []
            for phase_item in history:
                phase = phase_item.get("phase")
                started_at = phase_item.get("started_at")
                completed_at = phase_item.get("completed_at")
                if started_at and phase:
                    entries.append(
                        {
                            "timestamp": started_at,
                            "level": "INFO",
                            "event": f"Phase started: {phase}",
                            "phase": phase,
                        }
                    )
                if completed_at and phase:
                    success = phase_item.get("success", True)
                    level = "INFO" if success else "ERROR"
                    event = (
                        f"Phase completed: {phase}"
                        if success
                        else f"Phase failed: {phase}"
                    )
                    entry = {
                        "timestamp": completed_at,
                        "level": level,
                        "event": event,
                        "phase": phase,
                    }
                    if phase_item.get("error_message"):
                        entry["error"] = phase_item["error_message"]
                    entries.append(entry)

            current_phase = state.get("current_phase")
            if current_phase:
                entries.append(
                    {
                        "timestamp": state.get("updated_at"),
                        "level": "INFO",
                        "event": f"Current phase: {current_phase}",
                        "phase": current_phase,
                    }
                )

        entries = entries[-max(limit, 1):]

    return JSONResponse({"entries": entries})


@app.get("/api/logs/{run_id}/raw")
async def get_logs_raw(run_id: str, limit: int = 200):
    """
    Return raw JSONL log lines for a run.
    """
    runs_dir = settings.get_runs_path()

    run_dir = None
    if runs_dir.exists():
        for d in runs_dir.iterdir():
            if d.is_dir() and d.name.endswith(f"_{run_id}"):
                run_dir = d
                break

    if not run_dir:
        raise HTTPException(status_code=404, detail="Run not found")

    logs_file = run_dir / "logs.jsonl"
    if not logs_file.exists():
        return JSONResponse({"lines": []})

    try:
        lines = logs_file.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {e}")

    return JSONResponse({"lines": lines[-max(limit, 1):]})


@app.get("/api/diagnostics/{run_id}")
async def get_diagnostics(run_id: str, limit: int = 10):
    """
    Return diagnostic information for a run (state + recent phase history).
    """
    runs_dir = settings.get_runs_path()

    run_dir = None
    if runs_dir.exists():
        for d in runs_dir.iterdir():
            if d.is_dir() and d.name.endswith(f"_{run_id}"):
                run_dir = d
                break

    if not run_dir:
        raise HTTPException(status_code=404, detail="Run not found")

    state_file = run_dir / "run_state.json"
    if not state_file.exists():
        raise HTTPException(status_code=404, detail="Run state not found")

    try:
        state = await read_json(state_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read state: {e}")

    history = state.get("phase_history") or []
    recent_history = history[-max(limit, 1):]

    last_error = None
    for item in reversed(history):
        if item.get("error_message"):
            last_error = item.get("error_message")
            break

    return JSONResponse(
        {
            "run_id": run_id,
            "current_phase": state.get("current_phase"),
            "updated_at": state.get("updated_at"),
            "running": run_id in running_tasks,
            "error_message": last_error,
            "phase_history": recent_history,
        }
    )


@app.get("/api/download/{run_id}")
async def download_package(run_id: str):
    """
    Download the completed concept package.
    """
    # Find the run directory
    runs_dir = settings.get_runs_path()
    
    run_dir = None
    if runs_dir.exists():
        for d in runs_dir.iterdir():
            if d.is_dir() and d.name.endswith(f"_{run_id}"):
                run_dir = d
                break
    
    if not run_dir:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Return the package index for now
    package_index = run_dir / "artifacts" / "delivery" / "package_index.md"
    if package_index.exists():
        return FileResponse(
            package_index,
            media_type="text/markdown",
            filename=f"konseptikeiju-{run_id}.md",
        )
    
    raise HTTPException(status_code=404, detail="Package not ready")


# CLI interface
def main():
    """Run the web server."""
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


async def run_cli(company_name: str, email: str = "cli@local", context: str = ""):
    """
    Run a forge from command line (for testing).
    """
    configure_logging()
    
    producer = await Producer.create(
        company_name=company_name,
        user_email=email,
        access_code=settings.access_code or "cli",
        additional_context=context,
    )
    
    await producer.run()
    
    return producer.state


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # CLI run mode: python -m src.main run "Company Name"
        if len(sys.argv) < 3:
            print("Usage: python -m src.main run 'Company Name'")
            sys.exit(1)
        
        company = sys.argv[2]
        context = sys.argv[3] if len(sys.argv) > 3 else ""
        
        print(f"Starting forge for: {company}")
        result = asyncio.run(run_cli(company, context=context))
        print(f"Complete! Run ID: {result.run_id}")
        print(f"Final phase: {result.current_phase}")
    else:
        # Default: run web server
        main()
