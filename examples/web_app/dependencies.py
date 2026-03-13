"""FastAPI dependency functions for session management and model caching."""

from fastapi import Cookie, Request

from okcourse.generators.anthropic import get_anthropic_text_models_async
from okcourse.generators.openai.openai_utils import AIModels, get_usable_models_async

from .session import SessionState, get_or_create_session


async def get_session(request: Request, session_id: str | None = Cookie(default=None)) -> SessionState:
    """FastAPI dependency that returns the current session, creating one if needed."""
    session = get_or_create_session(session_id)
    return session


async def get_cached_models() -> AIModels:
    """FastAPI dependency that returns cached AI models available to the current API key."""
    return await get_usable_models_async()


async def get_cached_anthropic_models() -> list[str]:
    """FastAPI dependency that returns cached Anthropic text models."""
    return await get_anthropic_text_models_async()
