"""Page routes that serve full HTML pages."""

from fastapi import APIRouter, Depends, Request

from ..dependencies import get_cached_anthropic_models, get_cached_models, get_session
from ..session import SessionState

router = APIRouter()


@router.get("/")
async def index(
    request: Request,
    session: SessionState = Depends(get_session),
    models=Depends(get_cached_models),
    anthropic_text_models: list[str] = Depends(get_cached_anthropic_models),
):
    """Serves the main page with the course configuration form."""
    from okcourse.generators.openai.openai_utils import get_voices_for_model, tts_models
    from okcourse.prompt_library import PROMPT_COLLECTION

    prompt_styles = [{"description": p.description, "index": i} for i, p in enumerate(PROMPT_COLLECTION)]
    default_tts = session.course.settings.tts_model
    voices = get_voices_for_model(default_tts)

    resp = request.app.state.templates.TemplateResponse(
        request,
        "index.html",
        {
            "text_models": models.text_models,
            "image_models": models.image_models,
            "tts_models": tts_models,
            "voices": voices,
            "prompt_styles": prompt_styles,
            "settings": session.course.settings,
            "anthropic_text_models": anthropic_text_models,
        },
    )
    # Set session cookie on the actual response object
    resp.set_cookie("session_id", session.session_id, httponly=True, samesite="lax")
    return resp
