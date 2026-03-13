"""FastAPI web application for generating audiobook-style courses with okcourse."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routes import api, htmx, pages
from .session import cleanup_expired_sessions

log = logging.getLogger(__name__)

APP_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages app startup and shutdown: template init, session cleanup task."""
    # Set up Jinja2 templates
    app.state.templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

    # Start background session cleanup
    async def _cleanup_loop():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            removed = cleanup_expired_sessions()
            if removed:
                log.info(f"Cleaned up {removed} expired session(s)")

    cleanup_task = asyncio.create_task(_cleanup_loop())

    yield

    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="okcourse", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

# Include routers
app.include_router(pages.router)
app.include_router(api.router)
app.include_router(htmx.router)
