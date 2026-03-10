"""JSON API endpoints for models, voices, progress SSE, and file downloads."""

import asyncio

from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import FileResponse, StreamingResponse

from okcourse.generators.openai.openai_utils import get_voices_for_model

from ..dependencies import get_cached_models
from ..session import get_session_by_id

router = APIRouter(prefix="/api")


@router.get("/models")
async def get_models(models=Depends(get_cached_models)):
    """Returns available AI models grouped by type."""
    return {
        "text_models": models.text_models,
        "image_models": models.image_models,
        "speech_models": models.speech_models,
    }


@router.get("/voices/{tts_model}")
async def get_voices(tts_model: str):
    """Returns voices compatible with the given TTS model."""
    return {"voices": get_voices_for_model(tts_model)}


@router.get("/prompt-styles")
async def get_prompt_styles():
    """Returns available course prompt styles."""
    from okcourse.prompt_library import PROMPT_COLLECTION

    return [{"description": p.description, "index": i} for i, p in enumerate(PROMPT_COLLECTION)]


@router.get("/progress")
async def progress_stream(session_id: str | None = Cookie(default=None)):
    """SSE endpoint that streams log messages for the current session."""

    async def event_generator():
        if not session_id:
            yield "data: No session\n\n"
            return

        session = get_session_by_id(session_id)
        if not session:
            yield "data: Session not found\n\n"
            return

        # Stream until generation completes
        while True:
            messages = session.log_handler.get_new_messages()
            for msg in messages:
                yield f"data: {msg}\n\n"

            if not session.generating:
                yield "event: done\ndata: complete\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/download/image")
async def download_image(session_id: str | None = Cookie(default=None)):
    """Serves the generated course image for download."""
    session = get_session_by_id(session_id) if session_id else None
    if not session or not session.course.generation_info.image_file_path:
        return {"error": "No image available"}

    path = session.course.generation_info.image_file_path
    if not path.exists():
        return {"error": "Image file not found"}

    return FileResponse(path, filename=path.name, media_type="image/png")


@router.get("/download/audio")
async def download_audio(session_id: str | None = Cookie(default=None)):
    """Serves the generated course audio for download."""
    session = get_session_by_id(session_id) if session_id else None
    if not session or not session.course.generation_info.audio_file_path:
        return {"error": "No audio available"}

    path = session.course.generation_info.audio_file_path
    if not path.exists():
        return {"error": "Audio file not found"}

    return FileResponse(path, filename=path.name, media_type="audio/mpeg")
